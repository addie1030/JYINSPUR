from odoo import models, fields


class PrintDesignField(models.Model):
    _name = "print.design.field"
    _description = "模型字段对应"

    print_design_bill_id = fields.Many2one("print.design.bill", string="单据名称")
    print_model_id = fields.Many2one("print.design.bill2model", string="模型名称")
    name_en = fields.Many2one("ir.model.fields", string="字段名")
    field_name_en = fields.Char(string="字段英文名")
    field_name_cn = fields.Char(string="字段中文名")
    field_type = fields.Selection([('string', 'text'), ('number', 'number')], default="string", string="字段类型")








