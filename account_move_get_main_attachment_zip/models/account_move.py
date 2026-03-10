from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_account_move_get_main_attachment_zip(self):
        invoices = self.filtered(lambda inv: inv.move_type != 'entry')
        # Ensure main attachment is set for invoices that have attachments but
        # no main attachment assigned yet (e.g. created programmatically).
        without_main = invoices.filtered(lambda inv: not inv.message_main_attachment_id)
        if without_main:
            existing_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', 'in', without_main.ids),
            ])
            existing_attachments.register_as_main_attachment(force=False)
            without_main.invalidate_recordset(fnames=['message_main_attachment_id'])

        attachments = invoices.filtered(
            lambda inv: inv.message_main_attachment_id
        ).mapped('message_main_attachment_id')

        # # For customer invoices without an attachment, generate individual PDF reports.
        # invoices_without_attachment = invoices.filtered(
        #     lambda inv: not inv.message_main_attachment_id
        #                 and inv.move_type in ('out_invoice', 'out_refund', 'out_receipt')
        #                 and inv.state == 'posted'
        # )
        # for invoice in invoices_without_attachment:
        #     pdf_content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
        #         'account.account_invoices', invoice.ids,
        #     )
        #     generated_attachment = self.env['ir.attachment'].create({
        #         'name': invoice._get_invoice_report_filename(),
        #         'raw': pdf_content,
        #         'mimetype': 'application/pdf',
        #         'res_model': 'account.move',
        #         'res_id': invoice.id,
        #     })
        #     attachments += generated_attachment

        if not attachments:
            raise UserError(_("No main attachment could be found for the selected invoices."))
        return {
            'type': 'ir.actions.act_url',
            'url': f'/account/download_invoice_attachments/{",".join(map(str, attachments.ids))}',
            'target': 'download',
        }
