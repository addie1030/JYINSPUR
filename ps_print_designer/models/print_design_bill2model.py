from odoo import models, fields, api


class PrintDesignBill2Model(models.Model):
    _name = "print.design.bill2model"
    _description = "单据对应模型"

    print_design_bill_id = fields.Many2one("print.design.bill", string="单据名称")
    model_id = fields.Many2one("ir.model", string="模型名称")
    name = fields.Char(string="Name", store=True, related="model_id.name")
    table_description = fields.Char(string="中文名表")
    symbol = fields.Selection([('1', '主表'), ('2', '从表'), ('3', '辅表')], string="模型标识")
    location = fields.Selection([('1', '表头'), ('2', '表体')], string="位置")
    relation = fields.Text(string="关联关系")
