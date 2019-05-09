from odoo import fields, models


class AssetGdlyzdPopeye(models.Model):
    _name = "ps.asset.gdlyzd"
    _description = "资产来源"

    _sql_constraints = [('name_unique', 'UNIQUE(name)', "已存在此资产减少原因名称")]

    name = fields.Char(string="来源名称")
    sffc = fields.Boolean(default=False, string='是否封存')


class AssetGdzjffPopeye(models.Model):
    _name = "ps.asset.gdzjff"
    _description = "折旧方法"

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "Name repetition !"),
    ]

    name = fields.Char(string="折旧方法名称")
    zjl = fields.Boolean(default=False, string='折旧率')
    zje = fields.Boolean(default=False, string='折旧额')
    yzje = fields.Text(string="月折旧额的计算公式")
    jesm = fields.Text(string="月折旧额的计算公式说明")
    yzjl = fields.Text(string="月折旧率的计算公式")
    jlsm = fields.Text(string="月折旧率的计算公式说明")
    jszq = fields.Char(default='M', string="计算周期")
    jsgs = fields.Char(string="哪一个公式")
    sffc = fields.Boolean(default=False, string='是否封存')

class AssetGdzclbPopeye(models.Model):
    _name = "ps.asset.gdzclb"
    _description = "资产类别"

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "Name repetition !"),
    ]

    name = fields.Char(string="类别名称")
    zjff = fields.Many2one('ps.asset.gdzjff', string='折旧方法')
    zjnx = fields.Char(string="折旧年限(月)")
    czl = fields.Char(string="残值率(%)")
    zczt = fields.Many2one('account.assets.status', string="资产状态")
    sffc = fields.Boolean(default=False, string='是否封存')

class AssetGdzcjsPopeye(models.Model):
    _name = "ps.asset.zc.zcjs"
    _description = "资产减少"

    name = fields.Many2one('ps.account.asset', string="资产名称")
    jsrq = fields.Date(string="减少日期")
    jsbm = fields.Many2one('hr.department', string="减少部门")
    sfbm = fields.Boolean(default=False, string="按部门减少")
    jsyz = fields.Char(string="减少原值")
    jssl = fields.Char(string="减少数量")
    jszj = fields.Char(string="减少折旧")
    jsjz = fields.Char(string="减少减值")
    jsyy = fields.Many2one('account.assets.reducefor', string="减少原因")
    zy = fields.Char(string="摘要")


    # @api.onchange('name')
    # def _set_bm_ids(self):
    #     self.ensure_one()
    #     if self.name.ps_asset_departments:
    #         self.bm_ids = self.name.ps_asset_departments.ids
