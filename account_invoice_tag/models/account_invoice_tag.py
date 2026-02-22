# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountInvoiceTag(models.Model):
    _name = "account.invoice.tag"
    _description = "Invoice Tag"
    _order = "name"

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Tag name must be unique."),
    ]

    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Color Index")
    deprecated = fields.Boolean(string="Deprecated")
