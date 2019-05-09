# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import re
from functools import partial

from lxml import etree

from odoo import models
from odoo.tools.pycompat import imap

def _generic_get(*nodes, xpath, namespaces, placeholder=None):
    if placeholder is not None:
        xpath = xpath.format(placeholder=placeholder)
    for node in nodes:
        item = node.xpath(xpath, namespaces=namespaces)
        if item:
            return item[0]
    return False

_get_amount = partial(_generic_get,
    xpath='ns:Amt/text()')

_get_credit_debit_indicator = partial(_generic_get,
    xpath='ns:CdtDbtInd/text()')

_get_transaction_date = partial(_generic_get,
    xpath=('ns:ValDt/ns:Dt/text()'
           '| ns:BookgDt/ns:Dt/text()'
           '| ns:BookgDt/ns:DtTm/text()'))

_get_partner_name = partial(_generic_get,
    xpath='.//ns:RltdPties/ns:{placeholder}/ns:Nm/text()')

_get_account_number = partial(_generic_get,
    xpath=('.//ns:RltdPties/ns:{placeholder}Acct/ns:Id/ns:IBAN/text()'
           '| (.//ns:{placeholder}Acct/ns:Id/ns:Othr/ns:Id)[1]/text()'))

_get_main_ref = partial(_generic_get,
    xpath='.//ns:RmtInf/ns:Strd/ns:{placeholder}RefInf/ns:Ref/text()')

_get_other_ref = partial(_generic_get,
    xpath=('ns:AcctSvcrRef/text()'
           '| {placeholder}ns:Refs/ns:TxId/text()'
           '| {placeholder}ns:Refs/ns:InstrId/text()'
           '| {placeholder}ns:Refs/ns:EndToEndId/text()'
           '| {placeholder}ns:Refs/ns:MndtId/text()'
           '| {placeholder}ns:Refs/ns:ChqNb/text()'))

def _get_signed_amount(*nodes, namespaces):
    amount = float(_get_amount(*nodes, namespaces=namespaces))
    sign = _get_credit_debit_indicator(*nodes, namespaces=namespaces)
    return amount if sign == 'CRDT' else -amount

def _get_counter_party(*nodes, namespaces):
    ind = _get_credit_debit_indicator(*nodes, namespaces=namespaces)
    return 'Dbtr' if ind == 'CRDT' else 'Cdtr'

def _set_amount_currency_and_currency_id(node, path, entry_vals, currency, curr_cache, has_multi_currency, namespaces):
    instruc_amount = node.xpath('%s/text()' % path, namespaces=namespaces)
    instruc_curr = node.xpath('%s/@Ccy' % path, namespaces=namespaces)
    if (has_multi_currency and instruc_amount and instruc_curr and
            instruc_curr[0] != currency and currency in curr_cache):
        entry_vals['amount_currency'] = abs(sum(imap(float, instruc_amount)))
        entry_vals['currency_id'] = curr_cache[instruc_curr[0]]

def _get_transaction_name(node, namespaces):
    xpaths = ('.//ns:RmtInf/ns:Ustrd/text()',
              './/ns:RmtInf/ns:Strd/ns:CdtrRefInf/ns:Ref/text()',
               'ns:AddtlNtryInf/text()')
    for xpath in xpaths:
        transaction_name = node.xpath(xpath, namespaces=namespaces)
        if transaction_name:
            return ' '.join(transaction_name)
    return '/'

def _get_ref(node, counter_party, prefix, namespaces):
    ref = _get_main_ref(node, placeholder=counter_party, namespaces=namespaces)
    if ref is False:  # Explicitely match False, not a falsy value
        ref = _get_other_ref(node, placeholder=prefix, namespaces=namespaces)
    return ref

def _get_unique_import_id(entry, sequence, name, date, unique_import_set, namespaces):
    unique_import_ref = entry.xpath('ns:AcctSvcrRef/text()', namespaces=namespaces)
    if unique_import_ref and not _is_full_of_zeros(unique_import_ref[0]) and unique_import_ref[0] != 'NOTPROVIDED':
        entry_ref = entry.xpath('ns:NtryRef/text()', namespaces=namespaces)
        if entry_ref:
            return '{}-{}'.format(unique_import_ref[0], entry_ref[0])
        elif not entry_ref and unique_import_ref[0] not in unique_import_set:
            return unique_import_ref[0]
        else:
            return '{}-{}'.format(unique_import_ref[0], sequence)
    else:
        return '{}-{}-{}'.format(name, date, sequence)

def _is_full_of_zeros(strg):
    pattern_zero = re.compile('^0+$')
    return bool(pattern_zero.match(strg))

class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _check_camt(self, data_file):
        try:
            root = etree.parse(io.BytesIO(data_file)).getroot()
        except:
            return None
        if root.tag.find('camt.053') != -1:
            return root
        return None

    def _parse_file(self, data_file):
        root = self._check_camt(data_file)
        if root is not None:
            return self._parse_file_camt(root)
        return super(AccountBankStatementImport, self)._parse_file(data_file)

    def _parse_file_camt(self, root):
        ns = {k or 'ns': v for k, v in root.nsmap.items()}

        curr_cache = {c['name']: c['id'] for c in self.env['res.currency'].search_read([], ['id', 'name'])}
        statement_list = []
        unique_import_set = set([])
        currency = account_no = False
        has_multi_currency = self.env.user.user_has_groups('base.group_multi_currency')
        for statement in root[0].findall('ns:Stmt', ns):
            statement_vals = {}
            statement_vals['name'] = statement.xpath('ns:Id/text()', namespaces=ns)[0]
            statement_vals['date'] = statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:Dt/ns:Dt/text()",
                                                              namespaces=ns)[0]

            # Transaction Entries 0..n
            transactions = []
            sequence = 0

            # Currency 0..1
            currency = statement.xpath('ns:Acct/ns:Ccy/text() | ns:Bal/ns:Amt/@Ccy', namespaces=ns)[0]

            for entry in statement.findall('ns:Ntry', ns):
                # Date 0..1
                date = _get_transaction_date(entry, namespaces=ns) or statement_vals['date']

                transaction_details = entry.xpath('.//ns:TxDtls', namespaces=ns)
                if not transaction_details:
                    sequence += 1
                    counter_party = _get_counter_party(entry, namespaces=ns)
                    entry_vals = {
                        'sequence': sequence,
                        'date': date,
                        'amount': _get_signed_amount(entry, namespaces=ns),
                        'name': _get_transaction_name(entry, namespaces=ns),
                        'partner_name': _get_partner_name(entry, placeholder=counter_party, namespaces=ns),
                        'account_number': _get_account_number(entry, placeholder=counter_party, namespaces=ns),
                        'ref': _get_ref(entry, counter_party=counter_party, prefix='ns:NtryDtls/ns:TxDtls/', namespaces=ns),
                    }

                    entry_vals['unique_import_id'] = _get_unique_import_id(
                        entry=entry,
                        sequence=sequence,
                        name=statement_vals['name'],
                        date=entry_vals['date'],
                        unique_import_set=unique_import_set,
                        namespaces=ns)

                    _set_amount_currency_and_currency_id(
                        node=entry,
                        path='ns:NtryDtls/ns:TxDtls/ns:AmtDtls/ns:InstdAmt/ns:Amt',
                        entry_vals=entry_vals,
                        currency=currency,
                        curr_cache=curr_cache,
                        has_multi_currency=has_multi_currency,
                        namespaces=ns)

                    unique_import_set.add(entry_vals['unique_import_id'])
                    transactions.append(entry_vals)

                for entry_details in transaction_details:
                    sequence += 1
                    counter_party = _get_counter_party(entry_details, entry, namespaces=ns)
                    entry_vals = {
                        'sequence': sequence,
                        'date': date,
                        'amount': _get_signed_amount(entry_details, entry, namespaces=ns),
                        'name': _get_transaction_name(entry_details, namespaces=ns),
                        'partner_name': _get_partner_name(entry_details, placeholder=counter_party, namespaces=ns),
                        'account_number': _get_account_number(entry_details, placeholder=counter_party, namespaces=ns),
                        'ref': _get_ref(entry_details, counter_party=counter_party, prefix='', namespaces=ns),
                    }

                    entry_vals['unique_import_id'] = _get_unique_import_id(
                        entry=entry,
                        sequence=sequence,
                        name=statement_vals['name'],
                        date=entry_vals['date'],
                        unique_import_set=unique_import_set,
                        namespaces=ns)

                    _set_amount_currency_and_currency_id(
                        node=entry_details,
                        path='ns:AmtDtls/ns:InstdAmt/ns:Amt',
                        entry_vals=entry_vals,
                        currency=currency,
                        curr_cache=curr_cache,
                        has_multi_currency=has_multi_currency,
                        namespaces=ns)

                    unique_import_set.add(entry_vals['unique_import_id'])
                    transactions.append(entry_vals)

            statement_vals['transactions'] = transactions

            # Start Balance
            # any (OPBD, PRCD, ITBD):
            #   OPBD : Opening Balance
            #   PRCD : Previous Closing Balance
            #   ITBD : Interim Balance (in the case of preceeding pagination)
            start_amount = float(statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='OPBD' or ns:Cd='PRCD' or ns:Cd='ITBD' or ns:Cd='OPAV']/../../ns:Amt/text()",
                                                              namespaces=ns)[0])
            # Credit Or Debit Indicator 1..1
            sign = statement.xpath('ns:Bal/ns:CdtDbtInd/text()', namespaces=ns)[0]
            if sign == 'DBIT':
                start_amount *= -1
            statement_vals['balance_start'] = start_amount
            # Ending Balance
            # Statement Date
            # any 'CLBD', 'CLAV'
            #   CLBD : Closing Balance
            #   CLAV : Closing Available
            end_amount = float(statement.xpath("ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:Amt/text()",
                                                              namespaces=ns)[0])
            sign = statement.xpath(
                "ns:Bal/ns:Tp/ns:CdOrPrtry[ns:Cd='CLBD' or ns:Cd='CLAV']/../../ns:CdtDbtInd/text()", namespaces=ns
            )[0]
            if sign == 'DBIT':
                end_amount *= -1
            statement_vals['balance_end_real'] = end_amount

            statement_list.append(statement_vals)

            # Account Number    1..1
            # if not IBAN value then... <Othr><Id> would have.
            account_no = statement.xpath('ns:Acct/ns:Id/ns:IBAN/text() | ns:Acct/ns:Id/ns:Othr/ns:Id/text()', namespaces=ns)[0]

        return currency, account_no, statement_list
