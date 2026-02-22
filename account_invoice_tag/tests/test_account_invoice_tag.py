# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("-at_install", "post_install")
class TestAccountInvoiceTag(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.Tag = cls.env["account.invoice.tag"]
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        cls.tag_a = cls.Tag.create({"name": "Urgent", "color": 1})
        cls.tag_b = cls.Tag.create({"name": "Pending", "color": 3})
        cls.tag_deprecated = cls.Tag.create({"name": "Old", "deprecated": True})

        cls.sale_journal = cls.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )

    def _make_invoice(self, move_type="out_invoice"):
        journal = (
            self.sale_journal
            if move_type in ("out_invoice", "out_refund")
            else self.purchase_journal
        )
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type=move_type,
                default_journal_id=journal.id,
            )
        )
        move_form.partner_id = self.partner
        with move_form.invoice_line_ids.new() as line:
            line.name = "Test line"
            line.price_unit = 100.0
        return move_form.save()

    # ------------------------------------------------------------------
    # Tag model
    # ------------------------------------------------------------------

    def test_tag_default_deprecated_is_false(self):
        tag = self.Tag.create({"name": "New Tag"})
        self.assertFalse(tag.deprecated)

    def test_tag_deprecated_flag(self):
        self.assertFalse(self.tag_a.deprecated)
        self.assertTrue(self.tag_deprecated.deprecated)

    def test_tag_name_must_be_unique(self):
        self.Tag.create({"name": "Unique"})
        with self.assertRaises(ValidationError):
            self.Tag.create({"name": "Unique"})

    def test_deprecated_tags_excluded_from_active_search(self):
        active_tags = self.Tag.search([("deprecated", "=", False)])
        self.assertIn(self.tag_a, active_tags)
        self.assertIn(self.tag_b, active_tags)
        self.assertNotIn(self.tag_deprecated, active_tags)

    # ------------------------------------------------------------------
    # Tags on invoices
    # ------------------------------------------------------------------

    def test_tags_on_customer_invoice(self):
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = self.tag_a | self.tag_b
        self.assertEqual(invoice.invoice_tag_ids, self.tag_a | self.tag_b)

    def test_tags_on_vendor_bill(self):
        bill = self._make_invoice("in_invoice")
        bill.invoice_tag_ids = self.tag_a
        self.assertIn(self.tag_a, bill.invoice_tag_ids)

    def test_tags_on_customer_credit_note(self):
        refund = self._make_invoice("out_refund")
        refund.invoice_tag_ids = self.tag_b
        self.assertIn(self.tag_b, refund.invoice_tag_ids)

    def test_tags_on_vendor_credit_note(self):
        refund = self._make_invoice("in_refund")
        refund.invoice_tag_ids = self.tag_a
        self.assertIn(self.tag_a, refund.invoice_tag_ids)

    def test_deprecated_tag_persists_on_existing_invoice(self):
        """A tag deprecated after assignment must remain on the invoice."""
        tag = self.Tag.create({"name": "Soon Deprecated"})
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = tag
        tag.write({"deprecated": True})
        self.assertIn(tag, invoice.invoice_tag_ids)

    def test_multiple_invoices_share_tag(self):
        invoice1 = self._make_invoice("out_invoice")
        invoice2 = self._make_invoice("out_invoice")
        invoice1.invoice_tag_ids = self.tag_a
        invoice2.invoice_tag_ids = self.tag_a
        self.assertIn(self.tag_a, invoice1.invoice_tag_ids)
        self.assertIn(self.tag_a, invoice2.invoice_tag_ids)

    def test_tags_not_copied_on_invoice_duplicate(self):
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = self.tag_a | self.tag_b
        copy = invoice.copy()
        self.assertFalse(copy.invoice_tag_ids)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def test_export_tags_produces_single_row(self):
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = self.tag_a | self.tag_b
        rows = invoice._export_rows([["invoice_tag_ids", "name"]])
        self.assertEqual(len(rows), 1)

    def test_export_tags_comma_separated(self):
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = self.tag_a | self.tag_b
        rows = invoice._export_rows([["invoice_tag_ids", "name"]])
        tag_names = {self.tag_a.name, self.tag_b.name}
        exported = set(rows[0][0].split(", "))
        self.assertEqual(exported, tag_names)

    def test_export_no_tags_returns_empty_string(self):
        invoice = self._make_invoice("out_invoice")
        rows = invoice._export_rows([["invoice_tag_ids", "name"]])
        self.assertEqual(rows[0][0], "")

    def test_export_other_fields_unaffected(self):
        invoice = self._make_invoice("out_invoice")
        invoice.invoice_tag_ids = self.tag_a
        rows = invoice._export_rows([["name"], ["invoice_tag_ids", "name"]])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], invoice.name)

    # ------------------------------------------------------------------
    # Access rights
    # ------------------------------------------------------------------

    def _make_user(self, name, login, group_ref):
        return self.env["res.users"].create(
            {
                "name": name,
                "login": login,
                "groups_id": [(6, 0, [self.env.ref(group_ref).id])],
            }
        )

    def test_account_user_can_read_tags(self):
        user = self._make_user(
            "Invoice User", "inv_user_read@test.com", "account.group_account_user"
        )
        tags = self.Tag.with_user(user).search([])
        self.assertIn(self.tag_a, tags)

    def test_account_user_cannot_create_tag(self):
        user = self._make_user(
            "Invoice User", "inv_user_create@test.com", "account.group_account_user"
        )
        with self.assertRaises(AccessError):
            self.Tag.with_user(user).create({"name": "Unauthorized"})

    def test_account_user_cannot_write_tag(self):
        user = self._make_user(
            "Invoice User", "inv_user_write@test.com", "account.group_account_user"
        )
        with self.assertRaises(AccessError):
            self.tag_a.with_user(user).write({"name": "Hacked"})

    def test_account_user_cannot_delete_tag(self):
        user = self._make_user(
            "Invoice User", "inv_user_unlink@test.com", "account.group_account_user"
        )
        tag = self.Tag.create({"name": "To Delete"})
        with self.assertRaises(AccessError):
            tag.with_user(user).unlink()

    def test_account_manager_can_manage_tags(self):
        user = self._make_user(
            "Invoice Manager",
            "inv_manager@test.com",
            "account.group_account_manager",
        )
        tag = self.Tag.with_user(user).create({"name": "Manager Tag"})
        tag.with_user(user).write({"name": "Manager Tag Updated"})
        tag.with_user(user).unlink()
