# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_tag_ids = fields.Many2many(
        comodel_name="account.invoice.tag",
        relation="account_move_invoice_tag_rel",
        column1="move_id",
        column2="tag_id",
        string="Tags",
        copy=False,
        domain="[('deprecated', '=', False)]",
    )

    invoice_tag_names = fields.Char(compute="_compute_invoice_tag_names")

    def _compute_invoice_tag_names(self):
        for record in self:
            record.invoice_tag_names = ",".join(record.invoice_tag_ids.mapped("name"))

    def _export_rows(self, fields, *, _is_toplevel_call=True):
        # Redirect invoice_tag_ids export paths to the computed Char field so
        # that Odoo never expands the Many2many into one row per tag, regardless
        # of import_compat mode.
        modified_fields = [
            ["invoice_tag_names"] if (path and path[0] == "invoice_tag_ids") else path
            for path in fields
        ]
        return super()._export_rows(modified_fields, _is_toplevel_call=_is_toplevel_call)
