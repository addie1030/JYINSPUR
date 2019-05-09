# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import datetime
import traceback

from collections import Counter
from dateutil.relativedelta import relativedelta
from uuid import uuid4

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import format_date
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _name = "sale.subscription"
    _description = "Subscription"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rating.mixin']

    def _get_default_pricelist(self):
        return self.env['product.pricelist'].search([('currency_id', '=', self.env.user.company_id.currency_id.id)], limit=1).id

    name = fields.Char(required=True, track_visibility="always", default="New")
    code = fields.Char(string="Reference", required=True, track_visibility="onchange", index=True, copy=False)
    stage_id = fields.Many2one(
        'sale.subscription.stage', string='Stage', index=True,
        default=lambda s: s._get_default_stage_id(), group_expand='_read_group_stage_ids', track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    company_id = fields.Many2one('res.company', string="Company", default=lambda s: s.env['res.company']._company_default_get(), required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, auto_join=True)
    tag_ids = fields.Many2many('account.analytic.tag', string='Tags')
    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date = fields.Date(string='End Date', track_visibility='onchange', help="If set in advance, the subscription will be set to pending 1 month before the date and will be closed on the date set in this field.")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', default=_get_default_pricelist, required=True)
    currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Currency', readonly=True)
    recurring_invoice_line_ids = fields.One2many('sale.subscription.line', 'analytic_account_id', string='Invoice Lines', copy=True)
    recurring_rule_type = fields.Selection(string='Recurrence', help="Invoice automatically repeat at specified interval", related="template_id.recurring_rule_type", readonly=1)
    recurring_interval = fields.Integer(string='Repeat Every', help="Repeat every (Days/Week/Month/Year)", related="template_id.recurring_interval", readonly=1)
    recurring_next_date = fields.Date(string='Date of Next Invoice', default=fields.Date.today, help="The next invoice will be created on this date then the period will be extended.")
    recurring_total = fields.Float(compute='_compute_recurring_total', string="Recurring Price", store=True, track_visibility='onchange')
    recurring_monthly = fields.Float(compute='_compute_recurring_monthly', string="Monthly Recurring Revenue", store=True)
    close_reason_id = fields.Many2one("sale.subscription.close.reason", string="Close Reason", track_visibility='onchange')
    template_id = fields.Many2one('sale.subscription.template', string='Subscription Template', required=True, track_visibility='onchange')
    payment_mode = fields.Selection(related='template_id.payment_mode', readonly=False)
    description = fields.Text()
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange', default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=False)
    team_user_id = fields.Many2one('res.users', string="Team Leader", related="team_id.user_id", readonly=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    country_id = fields.Many2one('res.country', related='partner_id.country_id', store=True, readonly=False)
    industry_id = fields.Many2one('res.partner.industry', related='partner_id.industry_id', store=True, readonly=False)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    # customer portal
    uuid = fields.Char('Account UUID', default=lambda self: str(uuid4()), copy=False, required=True)
    website_url = fields.Char('Website URL', compute='_website_url', help='The full URL to access the document through the website.')
    payment_token_id = fields.Many2one('payment.token', 'Payment Token', help='If not set, the default payment token of the partner will be used.', domain="[('partner_id','=',partner_id)]", oldname='payment_method_id')
    # add tax calculation
    recurring_amount_tax = fields.Float('Taxes', compute="_amount_all")
    recurring_amount_total = fields.Float('Total', compute="_amount_all")
    recurring_rule_boundary = fields.Selection(related="template_id.recurring_rule_boundary", readonly=False)
    starred_user_ids = fields.Many2many(
        'res.users', 'subscription_starred_user_rel', 'subscription_id', 'user_id',
        default=lambda s: s._get_default_starred_user_ids(),
        string='Members')
    starred = fields.Boolean(compute='_compute_starred', inverse='_inverse_starred', string='Show Subscription on dashboard',
                             help="Whether this subscription should be displayed on the dashboard or not")
    kpi_1month_mrr_delta = fields.Float('KPI 1 Month MRR Delta')
    kpi_1month_mrr_percentage = fields.Float('KPI 1 Month MRR Percentage')
    kpi_3months_mrr_delta = fields.Float('KPI 3 months MRR Delta')
    kpi_3months_mrr_percentage = fields.Float('KPI 3 Months MRR Percentage')
    percentage_satisfaction = fields.Integer(
        compute="_compute_percentage_satisfaction", string="% Happy", store=True, default=-1,
        help="Calculate the ratio between the number of the best ('great') ratings and the total number of ratings")
    health = fields.Selection([
        ('normal', 'Neutral'),
        ('done', 'Good'),
        ('bad', 'Bad')], string="Health", copy=False, default='normal', translate=True, help="Set a health status")
    in_progress = fields.Boolean(related='stage_id.in_progress')
    to_renew = fields.Boolean(string='To Renew', default=False, copy=False)

    _sql_constraints = [
        ('uuid_uniq', 'unique (uuid)', """UUIDs (Universally Unique IDentifier) for Sale Subscriptions should be unique!"""),
    ]

    @api.depends('rating_ids.rating')
    def _compute_percentage_satisfaction(self):
        for subscription in self:
            activities = subscription.rating_get_grades()
            total_activity_values = sum(activities.values())
            subscription.percentage_satisfaction = activities['great'] * 100 / total_activity_values if total_activity_values else -1

    def _compute_sale_order_count(self):
        sol = self.env['sale.order.line']
        if sol.check_access_rights('read', raise_exception=False):
            raw_data = sol.read_group(
                [('subscription_id', 'in', self.ids)],
                ['subscription_id', 'order_id'],
                ['subscription_id', 'order_id'],
                lazy=False,
            )
            count = Counter(g['subscription_id'][0] for g in raw_data)
        else:
            count = Counter()

        for subscription in self:
            subscription.sale_order_count = count[subscription.id]

    def _get_default_stage_id(self):
        return self.env['sale.subscription.stage'].search([], order='sequence', limit=1)

    def _get_default_starred_user_ids(self):
        return [(6, 0, [self.env.uid])]

    def _compute_starred(self):
        for subscription in self:
            subscription.starred = self.env.user in subscription.starred_user_ids

    def _inverse_starred(self):
        starred_subscriptions = not_star_subscriptions = self.env['sale.subscription'].sudo()
        for subscription in self:
            if self.env.user in subscription.starred_user_ids:
                starred_subscriptions |= subscription
            else:
                not_star_subscriptions |= subscription
        not_star_subscriptions.write({'starred_user_ids': [(4, self.env.uid)]})
        starred_subscriptions.write({'starred_user_ids': [(3, self.env.uid)]})

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.sudo().search([], order=order)

    def action_open_sales(self):
        self.ensure_one()
        sales = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)])
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[self.env.ref('sale_subscription.sale_order_view_tree_subscription').id, "tree"],
                      [self.env.ref('sale.view_order_form').id, "form"],
                      [False, "kanban"], [False, "calendar"], [False, "pivot"], [False, "graph"]],
            "domain": [["id", "in", sales.ids]],
            "context": {"create": False},
            "name": _("Sales Orders"),
        }

    def partial_invoice_line(self, sale_order, option_line, refund=False, date_from=False):
        """ Add an invoice line on the sales order for the specified option and add a discount
        to take the partial recurring period into account """
        order_line_obj = self.env['sale.order.line']
        values = {
            'order_id': sale_order.id,
            'product_id': option_line.product_id.id,
            'subscription_id': self.id,
            'product_uom_qty': option_line.quantity,
            'product_uom': option_line.uom_id.id,
            'discount': (1 - self.partial_recurring_invoice_ratio(date_from=date_from)) * 100,
            'price_unit': self.pricelist_id.with_context({'uom': option_line.uom_id.id}).get_product_price(option_line.product_id, 1, False),
            'name': option_line.name,
        }
        return order_line_obj.create(values)

    def partial_recurring_invoice_ratio(self, date_from=False):
        """Computes the ratio of the amount of time remaining in the current invoicing period
        over the total length of said invoicing period"""
        if date_from:
            date = fields.Date.from_string(date_from)
        else:
            date = datetime.date.today()
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        if fields.Date.from_string(self.recurring_next_date) == date:
            return 0
        invoicing_period = relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
        recurring_next_invoice = fields.Date.from_string(self.recurring_next_date)
        recurring_last_invoice = recurring_next_invoice - invoicing_period
        time_to_invoice = recurring_next_invoice - date - datetime.timedelta(days=1)
        ratio = float(time_to_invoice.days) / float((recurring_next_invoice - recurring_last_invoice).days)
        return ratio

    @api.model
    def default_get(self, fields):
        defaults = super(SaleSubscription, self).default_get(fields)
        if 'code' in fields:
            defaults.update(code=self.env['ir.sequence'].next_by_code('sale.subscription') or 'New')
        return defaults

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values:
            return 'sale_subscription.subtype_stage_change'
        return super(SaleSubscription, self)._track_subtype(init_values)

    def _compute_invoice_count(self):
        Invoice = self.env['account.invoice']
        can_read = Invoice.check_access_rights('read', raise_exception=False)
        for subscription in self:
            subscription.invoice_count = can_read and Invoice.search_count([('invoice_line_ids.subscription_id', '=', subscription.id)]) or 0

    @api.depends('recurring_invoice_line_ids', 'recurring_invoice_line_ids.quantity', 'recurring_invoice_line_ids.price_subtotal')
    def _compute_recurring_total(self):
        for account in self:
            account.recurring_total = sum(line.price_subtotal for line in account.recurring_invoice_line_ids)

    @api.depends('recurring_total', 'template_id.recurring_interval', 'template_id.recurring_rule_type')
    def _compute_recurring_monthly(self):
        # Generally accepted ratios for monthly reporting
        interval_factor = {
            'daily': 30.0,
            'weekly': 30.0 / 7.0,
            'monthly': 1.0,
            'yearly': 1.0 / 12.0,
        }
        for sub in self:
            sub.recurring_monthly = (
                sub.recurring_total * interval_factor[sub.recurring_rule_type] / sub.recurring_interval
            ) if sub.template_id else 0

    @api.depends('uuid')
    def _website_url(self):
        for account in self:
            account.website_url = '/my/subscription/%s/%s' % (account.id, account.uuid)

    @api.depends('recurring_invoice_line_ids', 'recurring_total')
    def _amount_all(self):
        for account in self:
            val = val1 = 0.0
            cur = account.pricelist_id.sudo().currency_id
            for line in account.recurring_invoice_line_ids:
                val1 += line.price_subtotal
                val += line._amount_line_tax()
            account.recurring_amount_tax = cur.round(val)
            account.recurring_amount_total = account.recurring_amount_tax + account.recurring_total

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist.id
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id

    @api.onchange('date_start', 'template_id')
    def onchange_date_start(self):
        if self.date_start and self.recurring_rule_boundary == 'limited':
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            self.date = fields.Date.from_string(self.date_start) + relativedelta(**{
                periods[self.recurring_rule_type]: self.template_id.recurring_rule_count * self.template_id.recurring_interval})
        else:
            self.date = False

    @api.onchange('template_id')
    def on_change_template(self):
        if self.template_id:
            # Check if record is a new record or exists in db by checking its _origin
            # note that this property is not always set, hence the getattr
            if not getattr(self, '_origin', self.browse()) and not isinstance(self.id, int):
                self.description = self.template_id.description

    @api.model
    def create(self, vals):
        vals['code'] = (
            vals.get('code') or
            self.env.context.get('default_code') or
            self.env['ir.sequence'].with_context(force_company=vals.get('company_id')).next_by_code('sale.subscription') or
            'New'
        )
        if vals.get('name', 'New') == 'New':
            vals['name'] = vals['code']
        subscription = super(SaleSubscription, self).create(vals)
        if vals.get('stage_id'):
            subscription._send_subscription_rating_mail(force_send=True)
        if subscription.partner_id:
            subscription.message_subscribe(subscription.partner_id.ids)
        return subscription

    def write(self, vals):
        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])
        result = super(SaleSubscription, self).write(vals)
        if vals.get('stage_id'):
            self._send_subscription_rating_mail(force_send=True)
        return result

    @api.multi
    def unlink(self):
        self.wipe()
        self.env['sale.subscription.snapshot'].sudo().search([
            ('subscription_id', 'in', self.ids)]).unlink()
        return super(SaleSubscription, self).unlink()

    @api.model_cr_context
    def _init_column(self, column_name):
        # to avoid generating a single default uuid when installing the module,
        # we need to set the default row by row for this column
        if column_name == "uuid":
            _logger.debug("Table '%s': setting default value of new column %s to unique values for each row",
                          self._table, column_name)
            self.env.cr.execute("SELECT id FROM %s WHERE uuid IS NULL" % self._table)
            acc_ids = self.env.cr.dictfetchall()
            query_list = [{'id': acc_id['id'], 'uuid': str(uuid4())} for acc_id in acc_ids]
            query = 'UPDATE ' + self._table + ' SET uuid = %(uuid)s WHERE id = %(id)s;'
            self.env.cr._obj.executemany(query, query_list)
            self.env.cr.commit()

        else:
            super(SaleSubscription, self)._init_column(column_name)

    def name_get(self):
        res = []
        for sub in self:
            name = '%s - %s' % (sub.code, sub.partner_id.sudo().display_name) if sub.code else sub.partner_id.display_name
            res.append((sub.id, '%s/%s' % (sub.template_id.sudo().code, name) if sub.template_id.sudo().code else name))
        return res

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env['account.invoice'].search([('invoice_line_ids.subscription_id', 'in', self.ids)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def cron_account_analytic_account(self):
        today = fields.Date.today()
        next_month = fields.Date.to_string(fields.Date.from_string(today) + relativedelta(months=1))

        # set to pending if date is in less than a month
        domain_pending = [('date', '<', next_month), ('in_progress', '=', True)]
        subscriptions_pending = self.search(domain_pending)
        subscriptions_pending.set_to_renew()

        # set to close if date is passed
        domain_close = [('date', '<', today), '|', ('in_progress', '=', True), ('to_renew', '=', True)]
        subscriptions_close = self.search(domain_close)
        subscriptions_close.set_close()

        return dict(pending=subscriptions_pending.ids, closed=subscriptions_close.ids)

    @api.model
    def _cron_recurring_create_invoice(self):
        return self._recurring_create_invoice(automatic=True)

    @api.model
    def _cron_update_kpi(self):
        subscriptions = self.search([('in_progress', '=', True)])
        subscriptions._take_snapshot(datetime.date.today())
        subscriptions._compute_kpi()

    @api.multi
    def _take_snapshot(self, date):
        for subscription in self:
            self.env['sale.subscription.snapshot'].create({
                'subscription_id': subscription.id,
                'date': fields.Date.to_string(date),
                'recurring_monthly': subscription.recurring_monthly,
            })

    def _get_subscription_delta(self, date):
        self.ensure_one()
        delta, percentage = False, False
        snapshot = self.env['sale.subscription.snapshot'].search([
            ('subscription_id', '=', self.id),
            ('date', '<=', date)], order='date desc', limit=1)
        if snapshot:
            delta = self.recurring_monthly - snapshot.recurring_monthly
            percentage = delta / snapshot.recurring_monthly
        return {'delta': delta, 'percentage': percentage}

    def _get_subscription_health(self):
        self.ensure_one()
        domain = [('id', '=', self.id)]
        if self.template_id.bad_health_domain != '[]' and self.search_count(domain + safe_eval(self.template_id.bad_health_domain)):
            health = 'bad'
        elif self.template_id.good_health_domain != '[]' and self.search_count(domain + safe_eval(self.template_id.good_health_domain)):
            health = 'done'
        else:
            health = 'normal'
        return health

    @api.multi
    def _compute_kpi(self):
        for subscription in self:
            delta_1month = subscription._get_subscription_delta(datetime.date.today() - relativedelta(months=1))
            delta_3months = subscription._get_subscription_delta(datetime.date.today() - relativedelta(months=3))
            health = subscription._get_subscription_health()
            subscription.write({
                'kpi_1month_mrr_delta': delta_1month['delta'],
                'kpi_1month_mrr_percentage': delta_1month['percentage'],
                'kpi_3months_mrr_delta': delta_3months['delta'],
                'kpi_3months_mrr_percentage': delta_3months['percentage'],
                'health': health,
            })

    def _send_subscription_rating_mail(self, force_send=False):
        for subscription in self.filtered(lambda subscription: subscription.stage_id.rating_template_id):
            subscription.rating_send_request(
                subscription.stage_id.rating_template_id,
                lang=subscription.partner_id.lang,
                force_send=force_send)

    def set_to_renew(self):
        return self.write({'to_renew': True})

    def unset_to_renew(self):
        return self.write({'to_renew': False})

    def clear_date(self):
        return self.write({'date': False})

    def set_close(self):
        today = fields.Date.from_string(fields.Date.today())
        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('in_progress', '=', False), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('in_progress', '=', False)], limit=1)
            sub.write({'stage_id': stage.id, 'to_renew': False, 'date': today})
        return True

    @api.multi
    def set_open(self):
        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('in_progress', '=', True), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('in_progress', '=', True)], limit=1)
            sub.write({'stage_id': stage.id, 'to_renew': False, 'date': False})

    def _prepare_invoice_data(self):
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_("You must first select a Customer for Subscription %s!") % self.name)

        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = self.company_id
            self = self.with_context(force_company=company.id, company_id=company.id)

        fpos_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
        journal = self.template_id.journal_id or self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        if not journal:
            raise UserError(_('Please define a sale journal for the company "%s".') % (company.name or '', ))

        next_date = fields.Date.from_string(self.recurring_next_date)
        if not next_date:
            raise UserError(_('Please define Date of Next Invoice of "%s".') % (self.display_name,))
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        end_date = next_date + relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
        end_date = end_date - relativedelta(days=1)     # remove 1 day as normal people thinks in term of inclusive ranges.
        addr = self.partner_id.address_get(['delivery', 'invoice'])

        sale_order = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)], order="id desc", limit=1)
        return {
            'account_id': self.partner_id.property_account_receivable_id.id,
            'type': 'out_invoice',
            'partner_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'currency_id': self.pricelist_id.currency_id.id,
            'journal_id': journal.id,
            'origin': self.code,
            'fiscal_position_id': fpos_id,
            'payment_term_id': sale_order.payment_term_id.id if sale_order else self.partner_id.property_payment_term_id.id,
            'company_id': company.id,
            'comment': _("This invoice covers the following period: %s - %s") % (format_date(self.env, next_date), format_date(self.env, end_date)),
            'user_id': self.user_id.id,
        }

    def _prepare_invoice_line(self, line, fiscal_position):
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(self.env.context['force_company'])
        else:
            company = line.analytic_account_id.company_id
            line = line.with_context(force_company=company.id, company_id=company.id)

        account = line.product_id.property_account_income_id
        if not account:
            account = line.product_id.categ_id.property_account_income_categ_id
        account_id = fiscal_position.map_account(account).id

        tax = line.product_id.taxes_id.filtered(lambda r: r.company_id == company)
        tax = fiscal_position.map_tax(tax, product=line.product_id, partner=self.partner_id)
        return {
            'name': line.name,
            'account_id': account_id,
            'account_analytic_id': line.analytic_account_id.analytic_account_id.id,
            'subscription_id': line.analytic_account_id.id,
            'price_unit': line.price_unit or 0.0,
            'discount': line.discount,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'invoice_line_tax_ids': [(6, 0, tax.ids)],
            'analytic_tag_ids': [(6, 0, line.analytic_account_id.tag_ids.ids)]
        }

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position)
        return [(0, 0, self._prepare_invoice_line(line, fiscal_position)) for line in self.recurring_invoice_line_ids]

    def _prepare_invoice(self):
        invoice = self._prepare_invoice_data()
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(invoice['fiscal_position_id'])
        return invoice

    def recurring_invoice(self):
        self._recurring_create_invoice()
        return self.action_subscription_invoice()

    def _prepare_renewal_order_values(self):
        res = dict()
        for subscription in self:
            order_lines = []
            fpos_id = self.env['account.fiscal.position'].get_fiscal_position(subscription.partner_id.id)
            for line in subscription.recurring_invoice_line_ids:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.product_tmpl_id.name,
                    'subscription_id': subscription.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                }))
            addr = subscription.partner_id.address_get(['delivery', 'invoice'])
            sale_order = self.env['sale.order'].search([('order_line.subscription_id', 'in', self.ids)], order="id desc", limit=1)
            res[subscription.id] = {
                'pricelist_id': subscription.pricelist_id.id,
                'partner_id': subscription.partner_id.id,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
                'currency_id': subscription.pricelist_id.currency_id.id,
                'order_line': order_lines,
                'analytic_account_id': subscription.analytic_account_id.id,
                'subscription_management': 'renew',
                'origin': subscription.code,
                'note': subscription.description,
                'fiscal_position_id': fpos_id,
                'user_id': subscription.user_id.id,
                'payment_term_id': sale_order.payment_term_id.id if sale_order else subscription.partner_id.property_payment_term_id.id,
            }
        return res

    def prepare_renewal_order(self):
        self.ensure_one()
        values = self._prepare_renewal_order_values()
        order = self.env['sale.order'].create(values[self.id])
        order.order_line._compute_tax_id()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order.id,
        }

    def increment_period(self):
        for subscription in self:
            current_date = subscription.recurring_next_date or self.default_get(['recurring_next_date'])['recurring_next_date']
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            new_date = fields.Date.from_string(current_date) + relativedelta(**{periods[subscription.recurring_rule_type]: subscription.recurring_interval})
            subscription.write({'recurring_next_date': new_date})

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('code', operator, name), ('name', operator, name), ('partner_id.name', operator, name)]
        subscription_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(subscription_ids).name_get()

    def wipe(self):
        """Wipe a subscription clean by deleting all its lines."""
        lines = self.mapped('recurring_invoice_line_ids')
        lines.unlink()
        return True

    @api.multi
    def open_website_url(self):
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url,
            'target': 'self',
        }

    def add_option(self, option_id):
        pass

    def set_option(self, subscription, new_option, price):
        pass

    def remove_option(self, option_id):
        pass

    def _compute_options(self):
        pass

    # online payments
    @api.one
    def _do_payment(self, payment_token, invoice, two_steps_sec=True):
        tx_obj = self.env['payment.transaction']
        reference = "SUB%s-%s" % (self.id, datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
        values = {
            'amount': invoice.amount_total,
            'acquirer_id': payment_token.acquirer_id.id,
            'type': 'server2server',
            'currency_id': invoice.currency_id.id,
            'reference': reference,
            'payment_token_id': payment_token.id,
            'partner_id': self.partner_id.id,
            'partner_country_id': self.partner_id.country_id.id,
            'invoice_ids': [(6, 0, [invoice.id])],
            'callback_model_id': self.env['ir.model'].sudo().search([('model', '=', self._name)], limit=1).id,
            'callback_res_id': self.id,
            'callback_method': 'reconcile_pending_transaction',
        }

        tx = tx_obj.create(values)

        baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        payment_secure = {'3d_secure': two_steps_sec,
                          'accept_url': baseurl + '/my/subscription/%s/payment/%s/accept/' % (self.uuid, tx.id),
                          'decline_url': baseurl + '/my/subscription/%s/payment/%s/decline/' % (self.uuid, tx.id),
                          'exception_url': baseurl + '/my/subscription/%s/payment/%s/exception/' % (self.uuid, tx.id),
                          }
        tx.s2s_do_transaction(**payment_secure)
        return tx

    @api.multi
    def reconcile_pending_transaction(self, tx, invoice=False):
        self.ensure_one()
        if not invoice:
            invoice = tx.invoice_ids and tx.invoice_ids[0]
        if tx.state in ['done', 'authorized']:
            invoice.write({'reference': tx.reference, 'name': tx.reference})
            self.increment_period()
            self.set_open()
        else:
            invoice.action_cancel()
            invoice.unlink()

    @api.multi
    def _recurring_create_invoice(self, automatic=False):
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.invoice']
        current_date = datetime.date.today()
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        if len(self) > 0:
            subscriptions = self
        else:
            domain = [('recurring_next_date', '<=', current_date),
                      '|', ('in_progress', '=', True), ('to_renew', '=', True)]
            subscriptions = self.search(domain)
        if subscriptions:
            sub_data = subscriptions.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id'] for s in sub_data if s['company_id'][0] == company_id]
                subs = self.with_context(company_id=company_id, force_company=company_id).browse(sub_ids)
                context_company = dict(self.env.context, company_id=company_id, force_company=company_id)
                for subscription in subs:
                    subscription = subscription[0]  # Trick to not prefetch other subscriptions, as the cache is currently invalidated at each iteration
                    if automatic and auto_commit:
                        cr.commit()
                    # payment + invoice (only by cron)
                    if subscription.template_id.payment_mode in ['validate_send_payment', 'success_payment'] and subscription.recurring_total and automatic:
                        try:
                            payment_token = subscription.payment_token_id
                            tx = None
                            if payment_token:
                                invoice_values = subscription.with_context(lang=subscription.partner_id.lang)._prepare_invoice()
                                new_invoice = self.env['account.invoice'].with_context(context_company).create(invoice_values)
                                new_invoice.message_post_with_view(
                                    'mail.message_origin_link',
                                    values={'self': new_invoice, 'origin': subscription},
                                    subtype_id=self.env.ref('mail.mt_note').id)
                                tx = subscription._do_payment(payment_token, new_invoice, two_steps_sec=False)[0]
                                # commit change as soon as we try the payment so we have a trace somewhere
                                if auto_commit:
                                    cr.commit()
                                if tx.state in ['done', 'authorized']:
                                    subscription.send_success_mail(tx, new_invoice)
                                    msg_body = 'Automatic payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.invoice data-oe-id=%d>View Invoice</a>.' % (tx.id, tx.reference, tx.amount, new_invoice.id)
                                    subscription.message_post(body=msg_body)
                                    if subscription.template_id.payment_mode == 'validate_send_payment':
                                        subscription.validate_and_send_invoice(new_invoice)
                                    if auto_commit:
                                        cr.commit()
                                else:
                                    _logger.error('Fail to create recurring invoice for subscription %s', subscription.code)
                                    if auto_commit:
                                        cr.rollback()
                                    new_invoice.unlink()
                            if tx is None or tx.state != 'done':
                                amount = subscription.recurring_total
                                date_close = (
                                    subscription.recurring_next_date +
                                    relativedelta(days=subscription.template_id.auto_close_limit or
                                                  15)
                                )
                                close_subscription = current_date >= date_close
                                email_context = self.env.context.copy()
                                email_context.update({
                                    'payment_token': subscription.payment_token_id and subscription.payment_token_id.name,
                                    'renewed': False,
                                    'total_amount': amount,
                                    'email_to': subscription.partner_id.email,
                                    'code': subscription.code,
                                    'currency': subscription.pricelist_id.currency_id.name,
                                    'date_end': subscription.date,
                                    'date_close': date_close
                                })
                                if close_subscription:
                                    _, template_id = imd_res.get_object_reference('sale_subscription', 'email_payment_close')
                                    template = template_res.browse(template_id)
                                    template.with_context(email_context).send_mail(subscription.id)
                                    _logger.debug("Sending Subscription Closure Mail to %s for subscription %s and closing subscription", subscription.partner_id.email, subscription.id)
                                    msg_body = 'Automatic payment failed after multiple attempts. Subscription closed automatically.'
                                    subscription.message_post(body=msg_body)
                                    subscription.set_close()
                                else:
                                    _, template_id = imd_res.get_object_reference('sale_subscription', 'email_payment_reminder')
                                    msg_body = 'Automatic payment failed. Subscription set to "To Renew".'
                                    if (datetime.date.today() - subscription.recurring_next_date).days in [0, 3, 7, 14]:
                                        template = template_res.browse(template_id)
                                        template.with_context(email_context).send_mail(subscription.id)
                                        _logger.debug("Sending Payment Failure Mail to %s for subscription %s and setting subscription to pending", subscription.partner_id.email, subscription.id)
                                        msg_body += ' E-mail sent to customer.'
                                    subscription.message_post(body=msg_body)
                                    subscription.set_to_renew()
                            if auto_commit:
                                cr.commit()
                        except Exception:
                            if auto_commit:
                                cr.rollback()
                            # we assume that the payment is run only once a day
                            traceback_message = traceback.format_exc()
                            _logger.error(traceback_message)
                            last_tx = self.env['payment.transaction'].search([('reference', 'like', 'SUBSCRIPTION-%s-%s' % (subscription.id, datetime.date.today().strftime('%y%m%d')))], limit=1)
                            error_message = "Error during renewal of subscription %s (%s)" % (subscription.code, 'Payment recorded: %s' % last_tx.reference if last_tx and last_tx.state == 'done' else 'No payment recorded.')
                            _logger.error(error_message)

                    # invoice only
                    elif subscription.template_id.payment_mode in ['draft_invoice', 'manual', 'validate_send']:
                        try:
                            invoice_values = subscription.with_context(lang=subscription.partner_id.lang)._prepare_invoice()
                            new_invoice = self.env['account.invoice'].with_context(context_company).create(invoice_values)
                            new_invoice.message_post_with_view(
                                'mail.message_origin_link',
                                values={'self': new_invoice, 'origin': subscription},
                                subtype_id=self.env.ref('mail.mt_note').id)
                            new_invoice.with_context(context_company).compute_taxes()
                            invoices += new_invoice
                            next_date = subscription.recurring_next_date or current_date
                            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
                            invoicing_period = relativedelta(**{periods[subscription.recurring_rule_type]: subscription.recurring_interval})
                            new_date = next_date + invoicing_period
                            subscription.write({'recurring_next_date': new_date.strftime('%Y-%m-%d')})
                            if subscription.template_id.payment_mode == 'validate_send':
                                subscription.validate_and_send_invoice(new_invoice)
                            if automatic and auto_commit:
                                cr.commit()
                        except Exception:
                            if automatic and auto_commit:
                                cr.rollback()
                                _logger.exception('Fail to create recurring invoice for subscription %s', subscription.code)
                            else:
                                raise
        return invoices

    def send_success_mail(self, tx, invoice):
        imd_res = self.env['ir.model.data']
        template_res = self.env['mail.template']
        current_date = datetime.date.today()
        next_date = self.recurring_next_date or current_date
        # if no recurring next date, have next invoice be today + interval
        if not self.recurring_next_date:
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            invoicing_period = relativedelta(**{periods[self.recurring_rule_type]: self.recurring_interval})
            next_date = next_date + invoicing_period
        _, template_id = imd_res.get_object_reference('sale_subscription', 'email_payment_success')
        email_context = self.env.context.copy()
        email_context.update({
            'payment_token': self.payment_token_id.name,
            'renewed': True,
            'total_amount': tx.amount,
            'next_date': next_date,
            'previous_date': self.recurring_next_date,
            'email_to': self.partner_id.email,
            'code': self.code,
            'currency': self.pricelist_id.currency_id.name,
            'date_end': self.date,
        })
        _logger.debug("Sending Payment Confirmation Mail to %s for subscription %s", self.partner_id.email, self.id)
        template = template_res.browse(template_id)
        return template.with_context(email_context).send_mail(invoice.id)

    def validate_and_send_invoice(self, invoice):
        self.ensure_one()
        invoice.action_invoice_open()
        email_context = self.env.context.copy()
        email_context.update({
            'total_amount': invoice.amount_total,
            'email_to': self.partner_id.email,
            'code': self.code,
            'currency': self.pricelist_id.currency_id.name,
            'date_end': self.date,
        })
        _logger.debug("Sending Invoice Mail to %s for subscription %s", self.partner_id.email, self.id)
        self.template_id.invoice_mail_template_id.with_context(email_context).send_mail(invoice.id)


class SaleSubscriptionLine(models.Model):
    _name = "sale.subscription.line"
    _description = "Subscription Line"

    def _get_default_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    product_id = fields.Many2one('product.product', string='Product', domain="[('recurring_invoice','=',True)]", required=True)
    analytic_account_id = fields.Many2one('sale.subscription', string='Subscription')
    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', help="Quantity that will be invoiced.", default=1.0)
    uom_id = fields.Many2one('uom.uom', default=_get_default_uom_id, string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'))
    price_subtotal = fields.Float(compute='_compute_price_subtotal', string='Sub Total', digits=dp.get_precision('Account'), store=True)

    @api.depends('price_unit', 'quantity', 'discount', 'analytic_account_id.pricelist_id')
    def _compute_price_subtotal(self):
        for line in self:
            price = line.env['account.tax']._fix_tax_included_price(line.price_unit, line.product_id.sudo().taxes_id, [])
            line.price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            if line.analytic_account_id.pricelist_id:
                line.price_subtotal = line.analytic_account_id.pricelist_id.sudo().currency_id.round(line.price_subtotal)

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id
        partner = self.analytic_account_id.partner_id
        if partner.lang:
            product = product.with_context(lang=partner.lang)

        self.name = product.get_product_multiline_description_sale()

    @api.onchange('product_id', 'quantity')
    def onchange_product_quantity(self):
        domain = {}
        subscription = self.analytic_account_id
        company_id = subscription.company_id.id
        pricelist_id = subscription.pricelist_id.id
        context = dict(self.env.context, company_id=company_id, force_company=company_id, pricelist=pricelist_id, quantity=self.quantity)
        if not self.product_id:
            self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            partner = subscription.partner_id.with_context(context)
            if partner.lang:
                context.update({'lang': partner.lang})

            product = self.product_id.with_context(context)
            self.price_unit = product.price

            if not self.uom_id:
                self.uom_id = product.uom_id.id
            if self.uom_id.id != product.uom_id.id:
                self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

        return {'domain': domain}

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if not self.uom_id:
            self.price_unit = 0.0
            return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}
        else:
            return self.onchange_product_quantity()  # don't forward port

    def get_template_option_line(self):
        """ Return the account.analytic.invoice.line.option which has the same product_id as
        the invoice line"""
        if not self.analytic_account_id and not self.analytic_account_id.template_id:
            return False
        template = self.analytic_account_id.template_id
        return template.sudo().subscription_template_option_ids.filtered(lambda r: r.product_id == self.product_id)

    def _amount_line_tax(self):
        self.ensure_one()
        val = 0.0
        product = self.product_id
        product_tmp = product.sudo().product_tmpl_id
        for tax in product_tmp.taxes_id.filtered(lambda t: t.company_id == self.analytic_account_id.company_id):
            fpos_obj = self.env['account.fiscal.position']
            partner = self.analytic_account_id.partner_id
            fpos_id = fpos_obj.with_context(force_company=self.analytic_account_id.company_id.id).get_fiscal_position(partner.id)
            fpos = fpos_obj.browse(fpos_id)
            if fpos:
                tax = fpos.map_tax(tax, product, partner)
            compute_vals = tax.compute_all(self.price_unit * (1 - (self.discount or 0.0) / 100.0), self.analytic_account_id.currency_id, self.quantity, product, partner)['taxes']
            if compute_vals:
                val += compute_vals[0].get('amount', 0)
        return val

    @api.model
    def create(self, values):
        if values.get('product_id') and not values.get('name'):
            line = self.new(values)
            line.onchange_product_id()
            values['name'] = line._fields['name'].convert_to_write(line['name'], line)
        return super(SaleSubscriptionLine, self).create(values)


class SaleSubscriptionCloseReason(models.Model):
    _name = "sale.subscription.close.reason"
    _order = "sequence, id"
    _description = "Subscription Close Reason"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)


class SaleSubscriptionTemplate(models.Model):
    _name = "sale.subscription.template"
    _description = "Subscription Template"
    _inherit = "mail.thread"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    description = fields.Text(translate=True, string="Terms and Conditions")
    recurring_rule_type = fields.Selection([('daily', 'Day(s)'), ('weekly', 'Week(s)'),
                                            ('monthly', 'Month(s)'), ('yearly', 'Year(s)'), ],
                                           string='Recurrence', required=True,
                                           help="Invoice automatically repeat at specified interval",
                                           default='monthly', track_visibility='onchange')
    recurring_interval = fields.Integer(string="Repeat Every", help="Repeat every (Days/Week/Month/Year)", required=True, default=1, track_visibility='onchange')
    recurring_rule_boundary = fields.Selection([
        ('unlimited', 'Forever'),
        ('limited', 'Fixed')
    ], string='Duration', default='unlimited')
    recurring_rule_count = fields.Integer(string="End After", default=1)

    # Read-only copy of recurring_rule_type for proper readability of recurrence limitation:
    recurring_rule_type_readonly = fields.Selection(
        string="Recurrence Unit",
        related='recurring_rule_type', readonly=True, track_visibility=False)

    user_closable = fields.Boolean(string="Closable by customer", help="If checked, the user will be able to close his account from the frontend")
    payment_mode = fields.Selection([
        ('manual', 'Manual'),
        ('draft_invoice', 'Draft invoice'),
        ('validate_send', 'Invoice'),
        ('validate_send_payment', 'Invoice & try to charge'),
        ('success_payment', 'Invoice only on successful payment'),
    ], required=True, default='draft_invoice')
    product_ids = fields.One2many('product.template', 'subscription_template_id', copy=True)
    journal_id = fields.Many2one('account.journal', string="Accounting Journal", domain="[('type', '=', 'sale')]", company_dependent=True,
                                 help="If set, subscriptions with this template will invoice in this journal; "
                                      "otherwise the sales journal with the lowest sequence is used.")
    tag_ids = fields.Many2many('account.analytic.tag', 'sale_subscription_template_tag_rel', 'template_id', 'tag_id', string='Tags')
    product_count = fields.Integer(compute='_compute_product_count')
    subscription_count = fields.Integer(compute='_compute_subscription_count')
    color = fields.Integer()
    auto_close_limit = fields.Integer(string="Automatic closing limit", default=15,
                                      help="Number of days before a subscription gets closed when the chosen payment mode trigger automatically the payment.")
    good_health_domain = fields.Char(string='Good Health', default='[]',
                                     help="Domain used to change subscription's Kanban state with a 'Good' rating")
    bad_health_domain = fields.Char(string='Bad Health', default='[]',
                                    help="Domain used to change subscription's Kanban state with a 'Bad' rating")
    invoice_mail_template_id = fields.Many2one('mail.template', string='Invoice Email Template', domain=[('model', '=', 'account.invoice')])

    @api.constrains('recurring_interval')
    def _check_recurring_interval(self):
        if self.recurring_interval <= 0:
            raise ValidationError(_("The recurring interval must be positive"))

    def _compute_subscription_count(self):
        subscription_data = self.env['sale.subscription'].read_group(domain=[('template_id', 'in', self.ids), ('stage_id', '!=', False)],
                                                                     fields=['template_id'],
                                                                     groupby=['template_id'])
        mapped_data = dict([(m['template_id'][0], m['template_id_count']) for m in subscription_data])
        for template in self:
            template.subscription_count = mapped_data.get(template.id, 0)

    def _compute_product_count(self):
        product_data = self.env['product.template'].sudo().read_group([('subscription_template_id', 'in', self.ids)], ['subscription_template_id'], ['subscription_template_id'])
        result = dict((data['subscription_template_id'][0], data['subscription_template_id_count']) for data in product_data)
        for template in self:
            template.product_count = result.get(template.id, 0)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            connector = '&' if operator in expression.NEGATIVE_TERM_OPERATORS else '|'
            domain = [connector, ('code', operator, name), ('name', operator, name)]
        subscription_template_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(subscription_template_ids).name_get()

    def name_get(self):
        res = []
        for sub in self:
            name = '%s - %s' % (sub.code, sub.name) if sub.code else sub.name
            res.append((sub.id, name))
        return res


class SaleSubscriptionStage(models.Model):
    _name = 'sale.subscription.stage'
    _description = 'Subscription Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are not records in that stage to display.')
    rating_template_id = fields.Many2one('mail.template', string='Rating Email Template', domain=[('model', '=', 'sale.subscription')])
    in_progress = fields.Boolean(string='In Progress', default=True)


class SaleSubscriptionSnapshot(models.Model):
    _name = 'sale.subscription.snapshot'
    _description = 'Subscription Snapshot'

    subscription_id = fields.Many2one('sale.subscription', string='Subscription', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    recurring_monthly = fields.Float(string='Monthly Recurring Revenue', required=True)


class SaleSubscriptionAlert(models.Model):
    _name = 'sale.subscription.alert'
    _description = 'Subscription Alert'
    _inherits = {'base.automation': 'automation_id'}

    @api.model
    def default_get(self, default_fields):
        res = super(SaleSubscriptionAlert, self).default_get(default_fields)
        res['model_id'] = self.env['ir.model'].search([('model', '=', 'sale.subscription')]).id
        res['trigger'] = 'on_create_or_write'
        return res

    automation_id = fields.Many2one('base.automation', 'Automated Action', required=True, ondelete='restrict')
    action = fields.Selection([
        ('next_activity', 'Create next activity'),
        ('set_tag', 'Set a tag on the subscription'),
        ('set_stage', 'Set a stage on the subscription'),
        ('set_to_renew', 'Mark as To Renew'),
        ('email', 'Send an email to the customer'),
    ], string='Action', required=True, default=None)
    trigger_condition = fields.Selection([
        ('on_create_or_write', 'Modification'),
        ('on_time', 'Timed Condition'),
    ], string='Trigger On', required=True, default='on_create_or_write')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
    subscription_template_ids = fields.Many2many('sale.subscription.template', string='Subscription Templates')
    customer_ids = fields.Many2many('res.partner', string='Customers', domain=[('customer', '=', True)])
    company_id = fields.Many2one('res.company', string='Company')
    mrr_min = fields.Monetary('MRR Range Min', currency_field='currency_id')
    mrr_max = fields.Monetary('MRR Range Max', currency_field='currency_id')
    product_ids = fields.Many2many('product.product', string='Specific Products', domain=[('product_tmpl_id.subscription_template_id', '!=', None)])

    mrr_change_amount = fields.Float('MRR Change Amount')
    mrr_change_unit = fields.Selection(selection='_get_selection_mrr_change_unit', string='MRR Change Unit', default='percentage')
    mrr_change_period = fields.Selection([('1month', '1 Month'), ('3months', '3 Months')], string='MRR Change Period', default='1month')
    rating_percentage = fields.Integer('Rating Percentage')
    rating_operator = fields.Selection([('>', '>'), ('<', '<')], string='Rating Operator', default='>')
    stage_from_id = fields.Many2one('sale.subscription.stage')
    stage_to_id = fields.Many2one('sale.subscription.stage')

    tag_id = fields.Many2one('account.analytic.tag', string='Tag')
    stage_id = fields.Many2one('sale.subscription.stage', string='Stage')
    activity_user = fields.Selection([
        ('contract', 'Responsible of Contract'),
        ('channel_leader', 'Sales Channel Leader'),
        ('users', 'Specific Users'),
    ], string='Assign To')
    activity_user_ids = fields.Many2many('res.users', string='Specific Users')

    subscription_count = fields.Integer(compute='_compute_subscription_count')

    def _get_selection_mrr_change_unit(self):
        return [('percentage', '%'), ('currency', self.env.user.company_id.currency_id.symbol)]

    def _compute_subscription_count(self):
        for alert in self:
            domain = safe_eval(alert.filter_domain) if alert.filter_domain else []
            alert.subscription_count = self.env['sale.subscription'].search_count(domain)

    def _configure_filter_domain(self):
        for alert in self:
            domain = []
            if alert.subscription_template_ids:
                domain += [('template_id', 'in', alert.subscription_template_ids.ids)]
            if alert.customer_ids:
                domain += [('partner_id', 'in', alert.customer_ids.ids)]
            if alert.company_id:
                domain += [('company_id', '=', alert.company_id.id)]
            if alert.mrr_min:
                domain += [('recurring_monthly', '>=', alert.mrr_min)]
            if alert.mrr_max:
                domain += [('recurring_monthly', '<=', alert.mrr_max)]
            if alert.product_ids:
                template_ids = alert.product_ids.mapped('product_tmpl_id.subscription_template_id').ids
                domain += [('template_id', 'in', template_ids)]
            if alert.mrr_change_amount:
                if alert.mrr_change_unit == 'percentage':
                    domain += [('kpi_%s_mrr_percentage' % (alert.mrr_change_period), '>', alert.mrr_change_amount / 100)]
                else:
                    domain += [('kpi_%s_mrr_delta' % (alert.mrr_change_period), '>', alert.mrr_change_amount)]
            if alert.rating_percentage:
                domain += [('percentage_satisfaction', alert.rating_operator, alert.rating_percentage)]
            if alert.stage_to_id:
                domain += [('stage_id', '=', alert.stage_to_id.id)]
            super(SaleSubscriptionAlert, alert).write({'filter_domain': domain})

    def _configure_filter_pre_domain(self):
        for alert in self:
            if alert.stage_from_id:
                domain = [('stage_id', '=', alert.stage_from_id.id)]
            else:
                domain = []
            super(SaleSubscriptionAlert, alert).write({'filter_pre_domain': domain})

    @api.multi
    def _configure_alert_from_action(self, vals):
        # Unlink the children server actions if not needed anymore
        self.filtered(lambda alert: alert.action != 'next_activity' and alert.child_ids).unlink()
        for alert in self:
            if alert.action == 'set_tag' and alert.tag_id:
                alert.set_field_action('tag_ids', alert.tag_id.id)
            elif alert.action == 'set_stage' and alert.stage_id:
                alert.set_field_action('stage_id', alert.stage_id.id)
            elif alert.action == 'set_to_renew':
                alert.set_field_action('to_renew', True)
            elif vals.get('action') == 'next_activity' or vals.get('activity_user_ids') or vals.get('activity_user'):
                alert.set_activity_action()
            elif vals.get('action') == 'email':
                super(SaleSubscriptionAlert, alert).write({'state': 'email'})

    @api.model
    def create(self, vals):
        if vals.get('trigger_condition'):
            vals['trigger'] = vals['trigger_condition']
        res = super(SaleSubscriptionAlert, self).create(vals)
        res._configure_filter_domain()
        res._configure_filter_pre_domain()
        res._configure_alert_from_action(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('trigger_condition'):
            vals['trigger'] = vals['trigger_condition']
        res = super(SaleSubscriptionAlert, self).write(vals)
        self._configure_filter_domain()
        self._configure_filter_pre_domain()
        self._configure_alert_from_action(vals)
        return res

    @api.multi
    def set_field_action(self, field_name, value):
        for alert in self:
            tag_field = self.env['ir.model.fields'].search([('model', '=', alert.model_name), ('name', '=', field_name)])
            super(SaleSubscriptionAlert, alert).write({
                'state': 'object_write',
                'fields_lines': [(5, 0, 0), (0, False, {
                    'col1': tag_field.id,
                    'value': value})
                ]})

    @api.multi
    def set_activity_action(self):
        for alert in self:
            alert.child_ids.unlink()
            if self.activity_user == 'users':
                action_ids = []
                for user in alert.activity_user_ids:
                    seq = len(action_ids)
                    action = self.env['ir.actions.server'].create({
                        'name': '%s-%s' % (alert.name, seq),
                        'sequence': seq,
                        'state': 'next_activity',
                        'model_id': alert.model_id.id,
                        'activity_summary': alert.activity_summary,
                        'activity_type_id': alert.activity_type_id.id,
                        'activity_note': alert.activity_note,
                        'activity_date_deadline_range': alert.activity_date_deadline_range,
                        'activity_date_deadline_range_type': alert.activity_date_deadline_range_type,
                        'activity_user_type': 'specific',
                        'activity_user_id': user.id,
                        'usage': 'base_automation',
                    })
                    action_ids.append(action.id)
                alert.write({
                    'state': 'multi',
                    'child_ids': [(6, False, action_ids)],
                })
            elif self.activity_user == 'contract':
                alert.write({
                    'state': 'next_activity',
                    'activity_user_type': 'generic',
                    'activity_user_field_name': 'user_id',
                })
            elif self.activity_user == 'channel_leader':
                alert.write({
                    'state': 'next_activity',
                    'activity_user_type': 'generic',
                    'activity_user_field_name': 'team_user_id',
                })
