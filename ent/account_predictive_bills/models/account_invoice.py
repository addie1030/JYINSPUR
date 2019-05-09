# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import frozendict
import re


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_account(self):
        if self._context.get('set_default_account', True):
            return super(AccountInvoiceLine, self)._default_account()

    def _get_predict_postgres_dictionary(self):
        lang = self._context.get('lang') and self._context.get('lang')[:2]
        return {'fr': 'french'}.get(lang, 'english')

    @api.multi
    def _predict_field(self, sql_query, description):
        psql_lang = self._get_predict_postgres_dictionary()
        parsed_description = re.sub("[*&()|!':]+", " ", description)
        parsed_description = ' | '.join(parsed_description.split())
        limit_parameter = self.env["ir.config_parameter"].sudo().get_param("account.bill.predict.history.limit", '10000')
        params = {
            'lang': psql_lang,
            'description': parsed_description,
            'company_id': self.company_id.id or self.env.user.company_id.id,
            'limit_parameter': int(limit_parameter),
        }
        try:
            self.env.cr.execute(sql_query, params)
            result = self.env.cr.fetchone()
            if result:
                return result[1]
        except Exception as e:
            # In case there is an error while parsing the to_tsquery (wrong character for example)
            # We don't want to have a traceback, instead return False
            return False
        return False

    @api.multi
    def _predict_product(self, description):
        if not description:
            return False

        sql_query = """
            SELECT
                max(f.rel) AS ranking,
                f.product_id,
                count(coalesce(f.product_id, 1)) AS count
            FROM (
                SELECT
                    p_search.product_id,
                    ts_rank(p_search.document, query_plain) AS rel
                FROM (
                    SELECT
                        ail.product_id,
                        (setweight(to_tsvector(%(lang)s, ail.name), 'B'))
                         AS document
                    FROM account_invoice_line ail
                    JOIN account_invoice inv
                        ON ail.invoice_id = inv.id

                    WHERE inv.type = 'in_invoice'
                        AND inv.state NOT IN ('draft', 'cancel')
                        AND ail.company_id = %(company_id)s
                    ORDER BY inv.date_invoice DESC
                    LIMIT %(limit_parameter)s
                ) p_search,
                to_tsquery(%(lang)s, %(description)s) query_plain
                WHERE (p_search.document @@ query_plain)
            ) AS f
            GROUP BY f.product_id
            ORDER BY ranking desc, count desc
        """
        return self._predict_field(sql_query, description)

    @api.multi
    def _predict_account(self, description, partner):
        # This method uses postgres tsvector in order to try to deduce the account_id of an invoice line
        # based on the text entered into the name (description) field.
        # We give some more weight to search with the same partner_id (roughly 20%) in order to have better result
        # We only limit the search on the previous 10000 entries, which according to our tests bore the best
        # results. However this limit parameter is configurable by creating a config parameter with the key:
        # account.bill.predict.history.limit

        # For information, the tests were executed with a dataset of 40 000 bills from a live database, We splitted
        # the dataset in 2, removing the 5000 most recent entries and we tried to use this method to guess the account
        # of this validation set based on the previous entries.
        # The result is roughly 90% of success.
        if not description or not partner:
            return False

        sql_query = """
            SELECT
                max(f.rel) AS ranking,
                f.account_id,
                count(f.account_id) AS count
            FROM (
                SELECT
                    p_search.account_id,
                    ts_rank(p_search.document, query_plain) AS rel
                FROM (
                    (SELECT
                        ail.account_id,
                        (setweight(to_tsvector(%(lang)s, ail.name), 'B')) ||
                        (setweight(to_tsvector('simple', 'partnerid'|| replace(ail.partner_id::text, '-', 'x')), 'A')) AS document
                    FROM account_invoice_line ail
                    JOIN account_invoice inv
                        ON ail.invoice_id = inv.id
                    WHERE inv.type = 'in_invoice'
                        AND inv.state NOT IN ('draft', 'cancel')
                        AND ail.company_id = %(company_id)s
                    ORDER BY inv.date_invoice DESC
                    LIMIT %(limit_parameter)s
                    ) UNION ALL (
                    SELECT
                        id as account_id,
                        (setweight(to_tsvector(%(lang)s, name), 'B')) AS document
                    FROM account_account
                    WHERE user_type_id IN (
                        SELECT id
                        FROM account_account_type
                        WHERE internal_group = 'expense')
                    )
                ) p_search,
                to_tsquery(%(lang)s, %(description)s) query_plain
                WHERE (p_search.document @@ query_plain)
            ) AS f
            GROUP BY f.account_id
            ORDER BY ranking desc, count desc
        """
        description += ' partnerid' + str(partner.id or '').replace('-', 'x')
        return self._predict_field(sql_query, description)

    def _get_invoice_line_name_from_product(self):
        """ Overridden from account in order to allow not renaming the invoice
        line when we predict a product and change the value of the product_id
        field (_get_invoice_line_name_from_product is called in account module
        by _onchange_product_id).
        """
        if not self.env.context.get('skip_product_onchange_rename'):
            return super(AccountInvoiceLine, self)._get_invoice_line_name_from_product()
        else:
            # The context gets reset between each onchange call, so we don't have to remove our 'skip_product_onchange_rename' key.
            return None

    @api.onchange('name')
    def _onchange_name(self):
        if self.invoice_id.type == 'in_invoice' and self.name:
            # don't call prediction when the name change is triggered by a change of product
            if self.name != self._get_invoice_line_name_from_product():
                # don't predict the account if it has already be filled
                predict_account = not bool(self.account_id)
                if self.env.user.has_group('account.group_products_in_bills') and not self.product_id:
                    predicted_product_id = self._predict_product(self.name)
                    # We only change the product if we manage to predict its value
                    if predicted_product_id:
                        # We pass a context key to tell that we don't want the product
                        # onchange function to override the description that was entered by the user
                        self.env.context = frozendict(self.env.context, skip_product_onchange_rename=True)
                        self.product_id = predicted_product_id
                        # the account has been set via the onchange, there's no need to predict it any longer
                        predict_account = False

                if predict_account:
                    predicted_account_id = self._predict_account(self.name, self.partner_id)
                    # We only change the account if we manage to predict its value
                    if predicted_account_id:
                        self.account_id = predicted_account_id
                    else:
                        self.account_id = self.with_context(set_default_account=True, journal_id=self.invoice_id.journal_id.id)._default_account()
