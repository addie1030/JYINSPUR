# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class PsBomTree(models.Model):
    _name = "ps.bom.tree"
    _description = 'ps.bom.tree'
    _auto = False

    name = fields.Char('Name', readonly=True)
    bom_id = fields.Many2one('mrp.bom', 'Parent Id', index=True, ondelete='cascade')
    child_id = fields.Many2one('mrp.bom', 'Child Id', index=True, ondelete='cascade')
    parent_id = fields.Many2one('ps.bom.tree', 'Parent Id', index=True, ondelete='cascade')
    version = fields.Integer('Version', default=1)
    product_id = fields.Integer('Product Id')

    @api.model
    def table_create(self):
        self._table = 'ps_bom_tree'
        tools.drop_view_if_exists(self.env.cr, self._table)
        is_mrp_plm_installed = self.env['ir.module.module'].search([('name', '=', 'mrp_plm'), ('state', '=', 'installed')])
        if is_mrp_plm_installed:
            self.env.cr.execute("""
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        A.id AS product_id,
                        B.id AS child_id, 
                        D.bom_id AS bom_id,
                        C.name AS name,
						D.bom_id AS parent_id,
						B.version AS version
                    FROM product_product A
					Left Join product_template C ON C.id = A.product_tmpl_id
                    LEFT JOIN mrp_bom B ON B.product_tmpl_id = A.product_tmpl_id
                    LEFT JOIN mrp_bom_line D ON D.product_id = A.ID    
                )
            """ % (self._table))
        else:
            self.env.cr.execute("""
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        A.id AS product_id,
                        B.id AS child_id, 
                        D.bom_id AS bom_id,
                        C.name AS name,
						D.bom_id AS parent_id,
						CAST(null AS int) AS version
                    FROM product_product A
					Left Join product_template C ON C.id = A.product_tmpl_id
                    LEFT JOIN mrp_bom B ON B.product_tmpl_id = A.product_tmpl_id
                    LEFT JOIN mrp_bom_line D ON D.product_id = A.ID 
                )
            """ % (self._table))

    def recursive_bom(self, tree_lines, new_arr):
        for line in tree_lines:
            if line[3] and line[2]:
                sql = """select * from ps_bom_tree where bom_id = %s""" % (line[2])
                self.env.cr.execute(sql)
                res = self.env.cr.fetchall()
                for item in res:
                    new_arr.append(item)
                self.recursive_bom(res, new_arr)
        return new_arr

    @api.model
    def tree_parent(self, bom_id):
        sql = """select * from ps_bom_tree where bom_id = %s""" % (bom_id)
        self.env.cr.execute(sql)
        tree_lines = self.env.cr.fetchall()
        new_arr = []
        arr = []
        new_tree_lines = []
        bool = False
        for line in tree_lines:
            if new_tree_lines:
                for l in new_tree_lines:
                    if l[4] == line[4]:
                        bool = True
                    else:
                        bool = False
                if not bool:
                    new_tree_lines.append(line)
            else:
                new_tree_lines.append(line)
        for m in new_tree_lines:
            if m[3]:
                sql = """select * from ps_bom_tree where child_id = %s""" % (m[3])
                self.env.cr.execute(sql)
                pid = self.env.cr.fetchone()
                obj = {'id': m[0], 'pId': pid[0]}
                arr.append(obj)
        res = self.recursive_bom(new_tree_lines, new_arr)
        for item in res:
            if item[3]:
                sql = """select * from ps_bom_tree where child_id = %s""" % (item[3])
                self.env.cr.execute(sql)
                aaa = self.env.cr.fetchall()
                if len(aaa) > 1:
                    for a in aaa:
                        for b in res:
                            if a == b:
                                tree_item = a
                        for c in tree_lines:
                            if a == c:
                                tree_item = a
                    pid = tree_item[0]
                else:
                    pid = aaa[0][0]
                obj = {'id': item[0], 'pId': pid}
                arr.append(obj)
        return arr

