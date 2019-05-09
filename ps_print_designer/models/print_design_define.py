import random

from odoo import models, fields
from odoo.http import request
from odoo.exceptions import UserError, ValidationError, Warning


def print_execute_sql(self, sql):
    request.env.cr.execute(sql)
    data = request.env.cr.dictfetchall()
    return data

class PrintDesignDefine(models.Model):
    _name = "print.design.define"
    _description = "打印格式定义"

    name = fields.Char(string="格式名称", required=True)
    bills = fields.Many2one("print.design.bill", string="打印单据", required=True)
    report = fields.Text(string="打印格式")
    fields_text = fields.Text(string="表头表体字段")
    fields_rmb = fields.Text(string="人民币大写")
    fields_table = fields.Text(string="明细字段")
    fields_bar_code = fields.Text(string="条码字段")
    fields_image = fields.Text(string="图片字段")

    def fun_print_define(self):
        """根据上下文传入的参数跳转至打印设计界面.
            :param dict self: 在self中获取需要的id.
            :return:
            :rtype: dict
            """
        id = self.env.context.get('id')
        bills = self.env.context.get('bills')
        sql_head = """
            SELECT 
              field_name_cn as name,field_type as type
            FROM
              print_design_field
            where print_model_id 
            in (SELECT 
                  ID
                FROM  
                  PRINT_DESIGN_BILL2MODEL
                WHERE
                  PRINT_DESIGN_BILL_ID = %s
                AND LOCATION = '1')      
        """ % bills
        data_head = print_execute_sql(self, sql_head)
        data_head = "{\"id\":%s,\"name\":\"表头\",\"type\":\"map\",\"children\":%s}" % (random.randint(100, 199), data_head)
        sql_body = """
                    SELECT 
                      field_name_cn as name,field_type as type
                    FROM
                      print_design_field
                    where print_model_id 
                    in (SELECT 
                          ID
                        FROM  
                          PRINT_DESIGN_BILL2MODEL
                        WHERE
                          PRINT_DESIGN_BILL_ID = %s
                        AND LOCATION = '2')

        """ % bills
        data_body = print_execute_sql(self, sql_body)
        data_body = "{\"id\":%s,\"name\":\"表体\",\"type\":\"array\",\"children\":%s}" % (random.randint(200, 299), data_body)
        data = '[' + data_head + ',' + data_body + ']'
        data = data.replace('\'', '\"')
        return {
            "type": "ir.actions.client",
            "tag": "design_template",
            "target": "current",
            "params": {
                "data": data,
                "id": id
            }
        }

    def fun_print_preview(self):
        if self.report:
            report = self.report
            if report != None:
                return {
                    "type": "ir.actions.client",
                    "tag": "preview_template",
                    "target": "current",
                    "params": report
                }
        else:
            raise ValidationError('格式为空，请先设置格式！')