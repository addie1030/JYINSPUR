# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import http, fields
from odoo.http import request


class SalemanDashboard(http.Controller):

    @http.route('/sale_subscription_dashboard/fetch_salesmen', type='json', auth='user')
    def fetch_salesmen(self):

        request.cr.execute("""
            SELECT id
            FROM res_users
            WHERE EXISTS (
                SELECT 1
                FROM account_invoice
                WHERE user_id = res_users.id
            )
        """)  # we could also use distinct(user_id) on account_invoice, but distinct is slower
        sql_results = request.cr.dictfetchall()

        salesman_ids = request.env['res.users'].search_read([('id', 'in', [x['id'] for x in sql_results])], ['id', 'name'], order='name')
        current_salesmen = [x for x in salesman_ids if x['id'] == request.env.user.id]

        return {
            'salesman_ids': salesman_ids,
            'default_salesman': current_salesmen[0] if current_salesmen else None,
            'currency_id': request.env.user.company_id.currency_id.id,
        }

    @http.route('/sale_subscription_dashboard/get_values_salesman', type='json', auth='user')
    def get_values_salesman(self, salesman_id, start_date, end_date):

        start_date = fields.Date.from_string(start_date)
        end_date = fields.Date.from_string(end_date)

        contract_modifications = []

        new_mrr, churned_mrr, expansion_mrr, down_mrr, net_new_mrr = 0, 0, 0, 0, 0

        domain = [
            ('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_id.state', 'not in', ('draft', 'cancel')),
            ('invoice_id.user_id', '=', salesman_id),
        ]

        starting_invoice_line_ids = request.env['account.invoice.line'].search(domain + [
            ('asset_start_date', '>=', start_date),
            ('asset_start_date', '<=', end_date),
        ], order='subscription_id')
        stopping_invoice_lines_ids = request.env['account.invoice.line'].search(domain + [
            ('asset_end_date', '>=', start_date),
            ('asset_end_date', '<=', end_date),
        ], order='subscription_id')

        # CANCELLED ONES
        for contract, previous_il_ids_it in groupby(stopping_invoice_lines_ids, lambda il: il.subscription_id):
            previous_il_ids = list(previous_il_ids_it)
            previous_mrr = sum([x['asset_mrr'] for x in previous_il_ids])
            previous_il_id = previous_il_ids[0]

            next_il_ids = request.env['account.invoice.line'].search([
                ('asset_start_date', '>=', previous_il_id.asset_end_date),
                ('asset_start_date', '<', previous_il_id.asset_end_date + relativedelta(months=+1)),
                ('subscription_id', '=', previous_il_id.subscription_id.id)
            ])
            if not next_il_ids:
                # CANCELLED ONES
                contract_modifications.append({
                    'type': 'churn',
                    'partner': previous_il_id.partner_id.name,
                    'subscription': previous_il_id.subscription_id.name,
                    'subscription_template': previous_il_id.subscription_id.template_id.name,
                    'previous_mrr': str(previous_mrr),
                    'current_mrr': str(0),
                    'diff': -previous_mrr,
                })
                churned_mrr += previous_mrr

        # UP & DOWN & NEW ONES
        for contract, next_il_ids_it in groupby(starting_invoice_line_ids, lambda il: il.subscription_id):
            next_il_ids = list(next_il_ids_it)
            next_mrr = sum([x['asset_mrr'] for x in next_il_ids])
            next_il_id = next_il_ids[0]

            new_contract_modification = {
                'partner': next_il_id.partner_id.name,
                'subscription': next_il_id.subscription_id.name,
                'subscription_template': next_il_id.subscription_id.template_id.name,
            }

            # Was there any invoice_line in the last 30 days for this subscription ?
            previous_il_ids = request.env['account.invoice.line'].search([
                ('asset_end_date', '<=', next_il_id.asset_start_date),
                ('asset_end_date', '>', next_il_id.asset_start_date - relativedelta(months=+1)),
                ('subscription_id', '=', next_il_id.subscription_id.id)]
            )
            # Careful : what happened if invoice_lines from multiple invoices during last 30 days ?
            if previous_il_ids:
                previous_mrr = sum([x['asset_mrr'] for x in previous_il_ids.read(['asset_mrr'])])

                new_contract_modification['previous_mrr'] = str(previous_mrr)
                new_contract_modification['current_mrr'] = str(next_mrr)
                new_contract_modification['diff'] = next_mrr - previous_mrr

                # cast in int is to avoid rounding precision in python (ex : 10.0000000006 instead of 10)
                if int(previous_mrr) < int(next_mrr):
                    # UP ONES
                    new_contract_modification['type'] = 'up'
                    expansion_mrr += (next_mrr - previous_mrr)

                elif int(previous_mrr) > int(next_mrr):
                    # DOWN ONES
                    new_contract_modification['type'] = 'down'
                    down_mrr -= (next_mrr - previous_mrr)

            else:
                new_contract_modification['previous_mrr'] = str(0)
                new_contract_modification['current_mrr'] = str(next_mrr)
                new_contract_modification['diff'] = next_mrr

                active_invoice_line_ids = request.env['account.invoice.line'].search([
                    ('asset_start_date', '<', next_il_id.asset_start_date),
                    ('asset_end_date', '>', next_il_id.asset_start_date),
                    ('subscription_id', '=', next_il_id.subscription_id.id)]
                )
                if active_invoice_line_ids:
                    # If there is already a subscription running but we add some products, it should
                    # be considered as upgrade.
                    # UP ONES
                    new_contract_modification['type'] = 'up'
                    expansion_mrr += next_mrr
                else:
                    # NEW ONES
                    new_contract_modification['type'] = 'new'
                    new_mrr += next_mrr

            contract_modifications.append(new_contract_modification)

        net_new_mrr = new_mrr - churned_mrr + expansion_mrr - down_mrr

        nrr_invoice_ids = []
        total_nrr = 0
        current_invoice_ids = request.env['account.invoice'].search([
            ('type', 'in', ('out_invoice', 'out_refund')),
            ('state', 'not in', ('draft', 'cancel')),
            ('user_id', '=', salesman_id),
            ('date_invoice', '>=', start_date),
            ('date_invoice', '<=', end_date),
        ])

        for invoice_id in current_invoice_ids:
            invoice_nrr = sum([x.price_subtotal_signed for x in invoice_id.invoice_line_ids if x.asset_mrr == 0])
            if invoice_nrr > 0:
                total_nrr += invoice_nrr
                invoice_line = invoice_id.invoice_line_ids[0]
                nrr_invoice_ids.append({
                    'partner': invoice_line.partner_id.name,
                    'subscription': invoice_line.subscription_id.name,
                    'subscription_template': invoice_line.subscription_id.template_id.name,
                    'nrr': str(invoice_nrr),
                })

        return {
            'new': new_mrr,
            'churn': -churned_mrr,
            'up': expansion_mrr,
            'down': -down_mrr,
            'net_new': net_new_mrr,
            'contract_modifications': contract_modifications,
            'nrr': total_nrr,
            'nrr_invoices': nrr_invoice_ids,
        }
