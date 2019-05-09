from odoo import models, fields


class PrintDesignBill(models.Model):
    _name = "print.design.bill"
    _description = "单据名称定义"

    name = fields.Char(string="单据名称")
    table_name = fields.Many2one("ir.model", string="主表名称")