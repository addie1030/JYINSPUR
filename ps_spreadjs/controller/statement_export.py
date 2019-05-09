# import random
# import datetime
# import base64
# import io

from odoo import http
from odoo.http import request
# from flask import request
import json
import odoo
import os
from odoo.modules import get_module_path

class statement_export(http.Controller):
    @http.route('/odoo/export_file', auth='public', type='json', method='POST')
    def export(self, code, date, jsonstr):
        # sql = "select report_format from ps_statement_statements where report_code='0001' and report_date='201805'"
        # request.env.cr.execute(sql)
        # data_ids = request.env.cr.fetchone()
        # jsonstr = data_ids[0]

        # image_data = json.encode()
        # image_data = io.BytesIO(image_data)
        # response = http.send_file(image_data, filename="test.txt", as_attachment=True)

        # response = request.make_response(base64.b64encode(json), [('Content-Type', 'text/xml')])

        # return response

        # attachment = request.env['ir.attachment'].sudo().search_read(
        #     [('id', '=', 487)],
        #     ["name", "datas", "res_model", "res_id", "type", "url"])
        #
        # data = io.BytesIO(base64.standard_b64decode(attachment[0]["datas"]))
        # return http.send_file(data, filename=attachment[0]["name"], as_attachment=True)

        # txt_filename = 'D:\\Code\\odoo-11.0\\myaddons\\account_statement\\finnal.ssjson'  # 这是保存txt文件的位置
        # file = open(txt_filename, 'w')
        # file.write(json)
        # file.close()

        new_dict = json.loads(jsonstr)
        line = request.env['ps.statement.statements'].search([('report_code', '=', code), ('report_date', '=', date)])
        if line:
            reportname = line.report_name
        else:
            reportname = "资产负债表"
        datatable = new_dict["sheets"][reportname]["data"]["dataTable"]

        cell_ids = request.env['ps.statement.sheet.cells'].search([('report_code', '=', code), ('report_date', '=', date)])
        for celline in cell_ids:
            formula = celline.cell_formula
            row = celline.row_order
            col = celline.col_order
            datatable[row][col]["formula"] = formula

        # with open("../Downloads/"+code+"_"+date+"_"+reportname+".ssjson", "w") as f:
        # with open("../" + code + "_" + date + "_" + reportname + ".ssjson", "w") as f:

        # with odoo.tools.osutil.tempdir() as dump_dir:
        #     with open(os.path.join(dump_dir, code + "_" + date + "_" + reportname + ".ssjson"), 'w') as f:
        #         json.dump(new_dict, f)

        path = os.getcwd()
        with open(os.path.join(path, code + "_" + date + "_" + reportname + ".ssjson"), 'w') as f:
            json.dump(new_dict, f)

        return True

        # with open("../finnal.ssjson", 'r') as load_f:
        #     load_dict = json.load(load_f)
        #
        # print(load_dict)


