import base64

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestGetMainAttachmentZip(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pdf_content = b'%PDF-1.4 test content'

    def _create_invoice_with_attachment(self, move_type='in_invoice', attach_name='document.pdf'):
        """Create an invoice and assign a main attachment to it."""
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_a.id,
            'invoice_date': '2024-01-01',
        })
        attachment = self.env['ir.attachment'].create({
            'name': attach_name,
            'raw': self.pdf_content,
            'mimetype': 'application/pdf',
            'res_model': 'account.move',
            'res_id': invoice.id,
        })
        invoice.message_main_attachment_id = attachment
        return invoice

    def test_single_invoice_returns_act_url(self):
        """A single invoice with attachment returns an ir.actions.act_url action."""
        invoice = self._create_invoice_with_attachment()
        result = invoice.action_account_move_get_main_attachment_zip()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['target'], 'download')
        self.assertIn(str(invoice.message_main_attachment_id.id), result['url'])

    def test_multiple_invoices(self):
        """Multiple invoices with attachments return a URL containing all attachment IDs."""
        inv1 = self._create_invoice_with_attachment(attach_name='bill_1.pdf')
        inv2 = self._create_invoice_with_attachment(attach_name='bill_2.pdf')
        invoices = inv1 + inv2
        result = invoices.action_account_move_get_main_attachment_zip()
        url = result['url']
        self.assertIn(str(inv1.message_main_attachment_id.id), url)
        self.assertIn(str(inv2.message_main_attachment_id.id), url)

    def test_no_attachments_raises_error(self):
        """Invoices without any main attachment raise a UserError."""
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2024-01-01',
        })
        with self.assertRaises(UserError):
            invoice.action_account_move_get_main_attachment_zip()

    def test_entries_are_excluded(self):
        """Journal entries (move_type='entry') are excluded from the download."""
        invoice = self._create_invoice_with_attachment()
        entry = self.env['account.move'].create({
            'move_type': 'entry',
        })
        entry_attachment = self.env['ir.attachment'].create({
            'name': 'entry.pdf',
            'raw': self.pdf_content,
            'mimetype': 'application/pdf',
            'res_model': 'account.move',
            'res_id': entry.id,
        })
        entry.message_main_attachment_id = entry_attachment
        records = invoice + entry
        result = records.action_account_move_get_main_attachment_zip()
        self.assertIn(str(invoice.message_main_attachment_id.id), result['url'])
        self.assertNotIn(str(entry_attachment.id), result['url'])

    def test_only_entries_raises_error(self):
        """If only journal entries are selected, a UserError is raised."""
        entry = self.env['account.move'].create({
            'move_type': 'entry',
        })
        entry_attachment = self.env['ir.attachment'].create({
            'name': 'entry.pdf',
            'raw': self.pdf_content,
            'mimetype': 'application/pdf',
            'res_model': 'account.move',
            'res_id': entry.id,
        })
        entry.message_main_attachment_id = entry_attachment
        with self.assertRaises(UserError):
            entry.action_account_move_get_main_attachment_zip()

    def test_auto_assign_main_attachment(self):
        """Invoices without main attachment get it assigned automatically if an attachment exists."""
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2024-01-01',
        })
        # Create an attachment linked to the invoice but don't set it as main
        self.env['ir.attachment'].create({
            'name': 'orphan_bill.pdf',
            'raw': self.pdf_content,
            'mimetype': 'application/pdf',
            'res_model': 'account.move',
            'res_id': invoice.id,
        })
        self.assertFalse(invoice.message_main_attachment_id)
        result = invoice.action_account_move_get_main_attachment_zip()
        # After calling the action, the main attachment should be assigned
        invoice.invalidate_recordset(fnames=['message_main_attachment_id'])
        self.assertTrue(invoice.message_main_attachment_id)
        self.assertEqual(result['type'], 'ir.actions.act_url')

    def test_mixed_with_and_without_attachment(self):
        """Only invoices with attachments are included; those without are skipped."""
        inv_with = self._create_invoice_with_attachment(attach_name='has_attachment.pdf')
        inv_without = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2024-01-01',
        })
        records = inv_with + inv_without
        result = records.action_account_move_get_main_attachment_zip()
        self.assertIn(str(inv_with.message_main_attachment_id.id), result['url'])

    def test_customer_and_vendor_invoices(self):
        """Both customer and vendor invoices with attachments are included."""
        vendor_bill = self._create_invoice_with_attachment(
            move_type='in_invoice', attach_name='vendor_bill.pdf',
        )
        customer_invoice = self._create_invoice_with_attachment(
            move_type='out_invoice', attach_name='customer_invoice.pdf',
        )
        records = vendor_bill + customer_invoice
        result = records.action_account_move_get_main_attachment_zip()
        url = result['url']
        self.assertIn(str(vendor_bill.message_main_attachment_id.id), url)
        self.assertIn(str(customer_invoice.message_main_attachment_id.id), url)