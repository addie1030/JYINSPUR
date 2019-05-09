import json

import os
import requests
import werkzeug
from PyPDF2 import PdfFileWriter, PdfFileReader

import odoo
from odoo import http

class PrintDesignServer(http.Controller):
    @http.route('/print_design_server', type='json', auth='public')
    def print_design_server(self, **kw):
        """响应js页面ajax请求、_rpc请求.
            :param:
            :return:
            :rtype:
            """
        return 1

    @http.route('/run', type='http', auth='public')
    def merger_pdf(self, **kw):
        reportServerUrl = request.env['ir.config_parameter'].sudo().get_param('reportServerUrl')
        # 接收批量处理的key值
        keys = kw['key']
        # 下载pdf
        keys = keys.split(',')
        inFileList = []
        for key in keys:
            # 服务器url地址：https://www.reportbro.com/report/run?key=8fd83ced-3239-4a07-899e-d675aaeaf0bd&outputFormat=pdf
            # inspur : http://47.92.211.101:8000/reportbro/report/run
            # 系统参数设置打印服务器地址
            if reportServerUrl != False:
                file_url = reportServerUrl+'?key='
            else:
                file_url = "https://print-tools.mypscloud.com/reportbro/report/run?key="
            file_footer = "&outputFormat=pdf"
            url = file_url+key+file_footer
            r = requests.get(url, stream=True)
            pdf = "/%s.pdf" % key
            # 获取temp临时文件路径
            import tempfile
            pdf = tempfile.gettempdir()+pdf
            inFileList.append(pdf)
            with open(pdf, "wb") as pdf:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        pdf.write(chunk)
        # 合并pdf
        filename = tempfile.gettempdir()+"/print.pdf"
        pdfFileWriter = PdfFileWriter()
        for inFile in inFileList:
            # 依次循环打开要合并文件
            pdfReader = PdfFileReader(open(inFile, 'rb'))
            numPages = pdfReader.getNumPages()
            for index in range(0, numPages):
                pageObj = pdfReader.getPage(index)
                pdfFileWriter.addPage(pageObj)
            # 统一写入到输出文件中
            pdfFileWriter.write(open(filename, 'wb'))

        with open(filename, 'rb') as pdf_document:
            pdf_content = pdf_document.read()

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
        ]
        return werkzeug.wrappers.Response(pdf_content, headers=pdfhttpheaders)




    @http.route('/print_design_save', type='json', auth='public')
    def print_design_save(self, **kw):
        id = kw['documentProperties']['patternCurrencySymbol']
        parameters = kw['parameters']
        print_sum_rmb(self, parameters, id)
        sql = "UPDATE print_design_define SET report = '%s' WHERE ID = '%s' " % (json.dumps(kw), id)
        request.env.cr.execute(sql)
        print_design_save(self, kw['docElements'], id)
        return 1

    @http.route('/print_account_data', type='json', auth='public')
    def print_account_data(self, **kw):
        id = kw['active_ids'][0]
        modelName = kw['active_ids'][1]
        data_all = print_data(self, modelName, id)
        return data_all

    @http.route('/print_format', type='json', auth='public')
    def print_format(self, **kw):
        id = kw['active_ids'][0]
        modelName = kw['active_ids'][1]
        sql_bills = """
            select id from ir_model where model = '%s'
        """ % modelName
        bills_id = print_execute_sql(self, sql_bills)
        sql_id = """
            select id from print_design_bill where table_name = '%s'
        """ % bills_id[0]['id']
        bills_ = print_execute_sql(self, sql_id)
        sql = """
            select name from print_design_define where bills = '%s'
        """ % bills_[0]['id']
        bills_format = print_execute_sql(self, sql)
        aa = {"bill": [{"id": id}, {"modelName": modelName}], "format": bills_format}
        return aa

    @http.route('/print_format_data', type='json', auth='public')
    def print_format_data(self, **kw):
        sql = """
            select id from print_design_define where name = '%s'
        """ % kw['formatId']
        formatId = print_execute_sql(self, sql)
        for foo in formatId:
            id = foo['id']
        # 批量打印 begin 2018年9月14日
        # (1)获取所有单据ID
        ids = kw['billId']
        # (2)获取所有单据data
        data_all = []
        for foo in ids:
            data = print_data(self, kw['modelName'], foo, id)
            data_all.append(data)
        return data_all


import re

from odoo.http import request, content_disposition


def print_sum_rmb(self, parameters, id):
    for foo in parameters:
        for fo in foo['children']:
            if fo['type'] == 'sum':
                field_sum_rmb = fo['expression']
                field_sum_rmb = field_sum_rmb.split(".")[1].split("}")[0]
                sql_rmb = """
                            UPDATE print_design_define SET fields_rmb = '%s' WHERE ID = '%s' 
                        """ % (field_sum_rmb, id)
                request.env.cr.execute(sql_rmb)

def print_sum_rmb_data(self, formatId, bill_id_id, id):
    sql_get_field = """
        select fields_rmb from print_design_define where id = '%s'
    """ % formatId
    sql_get_field_ = print_execute_sql(self, sql_get_field)
    name_en = ''
    for foo in sql_get_field_:
        if len(foo['fields_rmb']) != 0:
            i = foo['fields_rmb']
            sql = """
                select print_design_field.field_name_en,print_design_bill2model.model_id
                from print_design_field ,print_design_bill2model
                where print_design_field.print_design_bill_id = '%s' 
                and print_design_field.field_name_cn = '%s' 
                and print_design_field.print_model_id = print_design_bill2model.id
            """ % (bill_id_id, i)
            field_name_en = print_execute_sql(self, sql)
            for foo in field_name_en:
                rmb_model_id = foo['model_id']
                rmb_name_en = foo['field_name_en']
            sql_model_name = """
                select model from ir_model where id = '%s'
            """ % rmb_model_id
            sql_model_name = print_execute_sql(self, sql_model_name)
            for foo_model in sql_model_name:
                model_name = foo_model['model']
                model_name = model_name.replace('.', '_')
            sql_data = """
                select sum(%s) as 合计 from %s where account_move_line.move_id = '%s'
            """ % (rmb_name_en, model_name, id)
            sum_data = print_execute_sql(self, sql_data)
            for su in sum_data:
                sum_ = su['合计']
            ss = Num2MoneyFormat(self, sum_)
            sb = {'人民币大写':ss}
    return sb

def Num2MoneyFormat(self, change_number):
    """
    .转换数字为大写货币格式( format_word.__len__() - 3 + 2位小数 )
    change_number 支持 float, int, long, string
    """
    format_word = ["分", "角", "元",
               "拾","百","千","万",
               "拾","百","千","亿",
               "拾","百","千","万",
               "拾","百","千","兆"]

    format_num = ["零","壹","贰","叁","肆","伍","陆","柒","捌","玖"]
    if type( change_number ) == str:
        # - 如果是字符串,先尝试转换成float或int.
        if '.' in change_number:
            try:    change_number = float( change_number )
            except: raise ValueError
        else:
            try:    change_number = int( change_number )
            except: raise ValueError

    if type( change_number ) == float:
        real_numbers = []
        for i in range( len( format_word ) - 3, -3, -1 ):
            if change_number >= 10 ** i or i < 1:
                real_numbers.append( int( round( change_number/( 10**i ), 2)%10 ) )

    elif isinstance( change_number, (int) ):
        real_numbers = [ int( i ) for i in str( change_number ) + '00' ]

    else:
        raise ValueError

    zflag = 0                       #标记连续0次数，以删除万字，或适时插入零字
    start = len(real_numbers) - 3
    change_words = []
    for i in range(start, -3, -1):  #使i对应实际位数，负数为角分
        if 0 != real_numbers[start-i] or len(change_words) == 0:
            if zflag:
                change_words.append(format_num[0])
                zflag = 0
            change_words.append( format_num[ real_numbers[ start - i ] ] )
            change_words.append(format_word[i+2])

        elif 0 == i or (0 == i%4 and zflag < 3):    #控制 万/元
            change_words.append(format_word[i+2])
            zflag = 0
        else:
            zflag += 1

    if change_words[-1] not in ( format_word[0], format_word[1]):
        # - 最后两位非"角,分"则补"整"
        change_words.append("整")

    return ''.join(change_words)

def print_get_id(self, bill_id_id):
    sql = """
        select min(id) from print_design_define where bills = '%s'
    """ % bill_id_id
    format_id = print_execute_sql(self, sql)
    for foo in format_id:
        format_id = foo['min']
    return format_id

def print_execute_sql(self, sql):
    request.env.cr.execute(sql)
    data = request.env.cr.dictfetchall()
    return data

def print_design_save(self, param, id):
    fields_head = []
    fields_body = []
    fields_rmb = []
    for foo in param:
        if foo['elementType'] == 'text':
            field_head = foo['content']
            g = re.search("\${.*\}", foo['content'])
            if g:
                field_head = field_head.split(".")[1].split("}")[0]
                if field_head != '合计' and field_head != '人民币大写':
                    fields_head.append(field_head)
        elif foo['elementType'] == 'table':
            for con in foo['contentDataRows']:
                for row in con['columnData']:
                    field_body = row['content']
                    field_body = field_body.split("{")[1].split("}")[0]
                    fields_body.append(field_body)
    sql_head = """
        UPDATE print_design_define SET fields_text = '%s' WHERE ID = '%s' 
    """ % (str(fields_head).replace('\'', '\"'), id)
    request.env.cr.execute(sql_head)
    sql_body = """
        UPDATE print_design_define SET fields_table = '%s' WHERE ID = '%s' 
    """ % (str(fields_body).replace('\'', '\"'), id)
    request.env.cr.execute(sql_body)
    return 1

def print_data(self, modelName, id, formatId):
    sql_model_id = """
        SELECT ID FROM IR_MODEL WHERE MODEL = '%s'
    """ % modelName
    modelId = print_execute_sql(self, sql_model_id)
    sql_bill_id = """
        SELECT ID FROM print_design_bill WHERE table_name = '%s'
    """ % modelId[0]['id']
    bill_id = print_execute_sql(self, sql_bill_id)
    bill_id_id = bill_id[0]['id']
    sql_print_format = """
        SELECT REPORT FROM PRINT_DESIGN_DEFINE WHERE BILLS = '%s' and id = '%s'
    """ % (bill_id_id, formatId)
    print_format = print_execute_sql(self, sql_print_format)
    for f1 in print_format:
        format = f1
    sql_print_head = """
        SELECT FIELDS_TEXT FROM PRINT_DESIGN_DEFINE WHERE BILLS = '%s' and id = '%s'
    """ % (bill_id_id, formatId)
    print_head = print_execute_sql(self, sql_print_head)
    for foo in print_head:
        dict = {}
        if len(foo['fields_text']) > 2:
            fields_text = foo['fields_text'][1:-1].replace('\"', '')
            fields_text = fields_text.replace(' ', '')
            fields_text = fields_text.split(",")
            for fo in fields_text:
                data_text = print_data_text(self, fo, bill_id_id, id)
                for f in data_text:
                    dict.update(f)
    sql_get_field = """
            select fields_rmb from print_design_define where id = '%s'
        """ % formatId
    sql_get_field_ = print_execute_sql(self, sql_get_field)
    for fi in sql_get_field_:
        if fi['fields_rmb'] is not None:
            name_en = print_sum_rmb_data(self, formatId, bill_id_id, id)
            dict.update(name_en)
    dic = {'表头': dict}
    sql_print_body = """
        SELECT FIELDS_TABLE FROM PRINT_DESIGN_DEFINE WHERE BILLS = '%s' and id = '%s'
    """ % (bill_id_id, formatId)
    print_body = print_execute_sql(self, sql_print_body)
    for boo in print_body:
        fields_table = boo['fields_table'][1:-1].replace('\"', '')
        fields_table = fields_table.replace(' ', '')
        fields_table = fields_table.split(",")
        fie = ''
        fro = ''
        whe = ''
        for bo in fields_table:
            if len(bo) != 0:
                data_table = print_data_table(self, bo, bill_id_id, id)
                fie += data_table['from']+'.'+data_table['field'] + ', '
                fro += data_table['from'] + ', '
                whe += data_table['where'] + ' and '
        fie = fie[:-2]
        fro = fro + modelName.replace('.', '_')
        whe = whe + modelName.replace('.', '_')+'.id= %s' % id
        # 去重复
        fro = fro.replace(' ', '')
        fro = fro.split(",")
        fro = list(set(fro))
        fro = str(fro).replace('\'', '')
        fro = fro.replace('[', '')
        fro = fro.replace(']', '')
        # whe = whe.replace(' ', '')
        whe = whe.split(",")
        whe = list(set(whe))
        whe = str(whe).replace('\'', '')
        whe = whe.replace('[', '')
        whe = whe.replace(']', '')

        sql = """
            select %s from %s where %s
        """ % (fie, fro, whe)
        data_table = print_execute_sql(self, sql)
        dic_table = {'表体': data_table}
    dic.update(dic_table)
    return {
        "report": format['report'],
        "data": dic
    }

def print_data_table(self, bo, bill_id, id):
    sql = """
            select print_model_id,field_name_en,field_name_cn 
            from print_design_field
            where print_model_id 
                in (select id 
                    from print_design_bill2model
                    where print_design_bill_id = '%s'
                    and location = '2') 
            and field_name_cn = '%s'
        """ % (bill_id, bo)
    fields = print_execute_sql(self, sql)
    if len(fields) != 0:
        for foo in fields:
            print_model_id = foo['print_model_id']
            field_name_en = foo['field_name_en']
            field_name_cn = foo['field_name_cn']
        sql = """
            select model_id 
            from print_design_bill2model
            where id = '%s'
        """ % print_model_id
        model_id = print_execute_sql(self, sql)
        for fo in model_id:
            _model_id = fo['model_id']
        sql = """
            select model from ir_model where id = '%s'
        """ % _model_id
        _model_id = print_execute_sql(self, sql)
        for f in _model_id:
            _model_id_ = f['model'].replace('.', '_')
        sql_modelId_table = """
                        select id,relation 
                        from print_design_bill2model
                        where print_design_bill_id = '%s'
                        and location = '2' and model_id = '%s'
                    """ % (bill_id, fo['model_id'])
        modelId_table = print_execute_sql(self, sql_modelId_table)
        for too in modelId_table:
            print(too['relation'])
        _sql_ = {
            "field": field_name_en +" as "+ field_name_cn,
            "from": _model_id_,
            "where": too['relation']
        }
    else:
        _sql_ = {}

    return _sql_


def print_data_text(self, field, bill_id, id):
    sql_modelId_text = """
        select id 
        from print_design_bill2model
        where print_design_bill_id = '%s'
        and location = '1'
    """ % bill_id
    modelId_text = print_execute_sql(self, sql_modelId_text)
    sql = """
        select print_model_id,field_name_en,field_name_cn 
        from print_design_field
        where print_model_id 
            in (select id 
                from print_design_bill2model
                where print_design_bill_id = '%s'
                and location = '1') 
        and field_name_cn = '%s'
    """ % (bill_id, field)
    fields = print_execute_sql(self, sql)
    for foo in fields:
        print(foo['print_model_id'])
        print(foo['field_name_en'])
        print(foo['field_name_cn'])
    sql = """
        select model_id 
        from print_design_bill2model
        where id = '%s'
    """ % foo['print_model_id']
    model_id = print_execute_sql(self, sql)
    # print(model_id)
    for fo in model_id:
        _model_id = fo['model_id']
    sql = """
        select model from ir_model where id = '%s'
    """ % _model_id
    _model_id = print_execute_sql(self, sql)
    for f in _model_id:
        _model_id_ = f['model'].replace('.', '_')
    sql = """
        select %s as %s from %s where id = '%s'
    """ % (foo['field_name_en'], foo['field_name_cn'], _model_id_, id)
    data = print_execute_sql(self, sql)
    return data