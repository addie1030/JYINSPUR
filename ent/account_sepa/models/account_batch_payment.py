# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _

from odoo.exceptions import UserError, ValidationError

from odoo.tools import float_round, float_repr, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import remove_accents

import base64
import random
import re
import time
from lxml import etree

def check_valid_SEPA_str(string):
    if re.search('[^-A-Za-z0-9/?:().,\'+ ]', string) is not None:
        raise ValidationError(_("The text used in SEPA files can only contain the following characters :\n\n"
            "a b c d e f g h i j k l m n o p q r s t u v w x y z\n"
            "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z\n"
            "0 1 2 3 4 5 6 7 8 9\n"
            "/ - ? : ( ) . , ' + (space)"))


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    sct_generic = fields.Boolean(compute='_compute_sct_generic',
        help=u"Technical feature used during the file creation. A SEPA message is said to be 'generic' if it cannot be considered as "
             u"a standard european credit transfer. That is if the bank journal is not in €, a transaction is not in € or a payee is "
             u"not identified by an IBAN account number and a bank BIC.")

    sct_warning = fields.Text(compute='_compute_sct_generic')

    @api.depends('payment_ids', 'journal_id')
    def _compute_sct_generic(self):
        for record in self:
            warnings = record._get_genericity_info()
            record.sct_generic = bool(warnings)
            text_warning = None
            if warnings and len(warnings) == 1:
                text_warning = _('Please note that the following warning has been raised:')
                text_warning += '\n%s\n\n' % warnings
                text_warning += _('In result, the file might not be accepted by all bank as a valid SEPA Credit Transfer file')
            elif warnings:
                text_warning = _('Please note that the following warnings have been raised:')
                text_warning += '<ul>'
                for warning in warnings:
                    text_warning += '<li>%s</li>' % warning
                text_warning += '</ul>\n\n'
                text_warning += _('In result, the file might not be accepted by all bank as a valid SEPA Credit Transfer file')
            record.sct_warning = text_warning

    @api.model
    def _sanitize_communication(self, communication):
        """ Returns a sanitized version of the communication given in parameter,
            so that:
                - it contains only latin characters
                - it does not contain any //
                - it does not start or end with /
                - it is maximum 140 characters long
            (these are the SEPA compliance criteria)
        """
        communication = communication[:140]
        while '//' in communication:
            communication = communication.replace('//', '/')
        if communication.startswith('/'):
            communication = communication[1:]
        if communication.endswith('/'):
            communication = communication[:-1]
        communication = re.sub('[^-A-Za-z0-9/?:().,\'+ ]', '', remove_accents(communication))
        return communication

    def _get_genericity_info(self):
        """ Find out if generating a credit transfer initiation message for payments requires to use the generic rules, as opposed to the standard ones.
            The generic rules are used for payments which are not considered to be standard european credit transfers.
        """
        self.ensure_one()
        if self.payment_method_code != 'sepa_ct':
            return []
        error_list = []
        debtor_currency = self.journal_id.currency_id and self.journal_id.currency_id.name or self.journal_id.company_id.currency_id.name
        if debtor_currency != 'EUR':
            error_list.append(_('Your bank account is not labelled in EUR'))
        for payment in self.payment_ids:
            bank_account = payment.partner_bank_account_id
            if payment.currency_id.name != 'EUR' and self.journal_id.company_id.currency_id.name == 'EUR':
                error_list.append(_('The transaction %s is instructed in another currency than EUR') % payment.name)
            if not bank_account.bank_bic:
                error_list.append(_('The creditor bank account %s used in payment %s is not identified by a BIC') % (payment.partner_bank_account_id.acc_number, payment.name))
            if not bank_account.acc_type == 'iban':
                error_list.append(_('The creditor bank account %s used in payment %s is not identified by an IBAN') % (payment.partner_bank_account_id.acc_number, payment.name))
        return error_list

    def _get_methods_generating_files(self):
        rslt = super(AccountBatchPayment, self)._get_methods_generating_files()
        rslt.append('sepa_ct')
        return rslt

    def validate_batch(self):
        if self.payment_method_code == 'sepa_ct':
            if self.journal_id.bank_account_id.acc_type != 'iban':
                    raise UserError(_("The account %s, of journal '%s', is not of type IBAN.\nA valid IBAN account is required to use SEPA features.") % (self.journal_id.bank_account_id.acc_number, self.journal_id.name))

            no_bank_acc_payments = self.env['account.payment']
            wrong_comm_payments = self.env['account.payment']
            for payment in self.payment_ids:
                if not payment.partner_bank_account_id:
                    no_bank_acc_payments += payment

            no_bank_acc_error_format = _("The following payments have no recipient bank account set: %s. \n\n")
            error_message = ''
            error_message += no_bank_acc_payments and no_bank_acc_error_format % ', '.join(no_bank_acc_payments.mapped('name')) or ''

            if error_message:
                raise UserError(error_message)

        return super(AccountBatchPayment, self).validate_batch()

    def _generate_export_file(self):
        if self.payment_method_code == 'sepa_ct':
            payments = self.payment_ids.sorted(key=lambda r: r.id)

            if self.journal_id.company_id.sepa_pain_version == 'pain.001.001.03.ch.02':
                xml_doc = self._create_pain_001_001_03_ch_document(payments)
            elif self.journal_id.company_id.sepa_pain_version == 'pain.001.003.03':
                xml_doc = self._create_pain_001_003_03_document(payments)
            else:
                xml_doc = self._create_pain_001_001_03_document(payments)

            return {
                'file': base64.encodestring(xml_doc),
                'filename': "SCT-" + self.journal_id.code + "-" + str(fields.Date.today()) + ".xml",
                'warning': self.sct_warning,
            }

        return super(AccountBatchPayment, self)._generate_export_file()

    def _create_pain_001_001_03_document(self, doc_payments):
        """ Create a sepa credit transfer file that follows the European Payment Councile generic guidelines (pain.001.001.03)

            :param doc_payments: recordset of account.payment to be exported in the XML document returned
        """
        Document = self._create_iso20022_document('pain.001.001.03')
        return self._create_iso20022_credit_transfer(Document, doc_payments)

    def _create_pain_001_001_03_ch_document(self, doc_payments):
        """ Create a sepa credit transfer file that follows the swiss specific guidelines, as established
            by SIX Interbank Clearing (pain.001.001.03.ch.02)

            :param doc_payments: recordset of account.payment to be exported in the XML document returned
        """
        Document = etree.Element("Document", nsmap={
            None: "http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"})
        return self._create_iso20022_credit_transfer(Document, doc_payments)

    def _create_pain_001_003_03_document(self, doc_payments):
        """ Create a sepa credit transfer file that follows the german specific guidelines, as established
            by the German Bank Association (Deutsche Kreditwirtschaft) (pain.001.003.03)

            :param doc_payments: recordset of account.payment to be exported in the XML document returned
        """
        Document = self._create_iso20022_document('pain.001.003.03')
        return self._create_iso20022_credit_transfer(Document, doc_payments)

    def _create_iso20022_document(self, pain_version):
        Document = etree.Element("Document", nsmap={
            None: "urn:iso:std:iso:20022:tech:xsd:%s" % (pain_version,),
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"})
        return Document

    def _create_iso20022_credit_transfer(self, Document, doc_payments):
        CstmrCdtTrfInitn = etree.SubElement(Document, "CstmrCdtTrfInitn")

        # Create the GrpHdr XML block
        GrpHdr = etree.SubElement(CstmrCdtTrfInitn, "GrpHdr")
        MsgId = etree.SubElement(GrpHdr, "MsgId")
        val_MsgId = str(int(time.time() * 100))[-10:]
        val_MsgId = self._sanitize_communication(self.journal_id.company_id.name[-15:]) + val_MsgId
        val_MsgId = str(random.random()) + val_MsgId
        val_MsgId = val_MsgId[-30:]
        MsgId.text = val_MsgId
        CreDtTm = etree.SubElement(GrpHdr, "CreDtTm")
        CreDtTm.text = time.strftime("%Y-%m-%dT%H:%M:%S")
        NbOfTxs = etree.SubElement(GrpHdr, "NbOfTxs")
        val_NbOfTxs = str(len(doc_payments))
        if len(val_NbOfTxs) > 15:
            raise ValidationError(_("Too many transactions for a single file."))
        if not self.journal_id.bank_account_id.bank_bic:
            raise UserError(_("There is no Bank Identifier Code recorded for bank account '%s' of journal '%s'") % (self.journal_id.bank_account_id.acc_number, self.journal_id.name))
        NbOfTxs.text = val_NbOfTxs
        CtrlSum = etree.SubElement(GrpHdr, "CtrlSum")
        CtrlSum.text = self._get_CtrlSum(doc_payments)
        GrpHdr.append(self._get_InitgPty())

        # Create one PmtInf XML block per execution date
        payments_date_wise = {}
        for payment in doc_payments:
            if payment.payment_date not in payments_date_wise:
                payments_date_wise[payment.payment_date] = []
            payments_date_wise[payment.payment_date].append(payment)
        count = 0
        for payment_date, payments_list in payments_date_wise.items():
            count += 1
            PmtInf = etree.SubElement(CstmrCdtTrfInitn, "PmtInf")
            PmtInfId = etree.SubElement(PmtInf, "PmtInfId")
            PmtInfId.text = (val_MsgId + str(self.journal_id.id) + str(count))[-30:]
            PmtMtd = etree.SubElement(PmtInf, "PmtMtd")
            PmtMtd.text = 'TRF'
            BtchBookg = etree.SubElement(PmtInf, "BtchBookg")
            BtchBookg.text = 'false'
            NbOfTxs = etree.SubElement(PmtInf, "NbOfTxs")
            NbOfTxs.text = str(len(payments_list))
            CtrlSum = etree.SubElement(PmtInf, "CtrlSum")
            CtrlSum.text = self._get_CtrlSum(payments_list)
            PmtInf.append(self._get_PmtTpInf())
            ReqdExctnDt = etree.SubElement(PmtInf, "ReqdExctnDt")
            ReqdExctnDt.text = fields.Date.to_string(payment_date)
            PmtInf.append(self._get_Dbtr())
            PmtInf.append(self._get_DbtrAcct())
            DbtrAgt = etree.SubElement(PmtInf, "DbtrAgt")
            FinInstnId = etree.SubElement(DbtrAgt, "FinInstnId")
            BIC = etree.SubElement(FinInstnId, "BIC")
            BIC.text = self.journal_id.bank_account_id.bank_bic.replace(' ', '')

            # One CdtTrfTxInf per transaction
            for payment in payments_list:
                PmtInf.append(self._get_CdtTrfTxInf(PmtInfId, payment))

        return etree.tostring(Document, pretty_print=True, xml_declaration=True, encoding='utf-8')

    def _get_CtrlSum(self, payments):
        return float_repr(float_round(sum(payment.amount for payment in payments), 2), 2)

    def _get_company_PartyIdentification32(self, org_id=True, postal_address=True):
        """ Returns a PartyIdentification32 element identifying the current journal's company
        """
        ret = []
        company = self.journal_id.company_id
        name_length = self.sct_generic and 35 or 70
        payment_model = self.env['account.payment']

        Nm = etree.Element("Nm")
        Nm.text = self._sanitize_communication(company.sepa_initiating_party_name[:name_length])
        ret.append(Nm)

        if postal_address and company.partner_id.city and company.partner_id.country_id.code:
            PstlAdr = etree.Element("PstlAdr")
            Ctry = etree.SubElement(PstlAdr, "Ctry")
            Ctry.text = company.partner_id.country_id.code
            if company.partner_id.street:
                AdrLine = etree.SubElement(PstlAdr, "AdrLine")
                AdrLine.text = self._sanitize_communication(company.partner_id.street)
            if company.partner_id.zip and company.partner_id.city:
                AdrLine = etree.SubElement(PstlAdr, "AdrLine")
                AdrLine.text = self._sanitize_communication(company.partner_id.zip) + " " + self._sanitize_communication(company.partner_id.city)
            ret.append(PstlAdr)

        if org_id and company.sepa_orgid_id:
            Id = etree.Element("Id")
            OrgId = etree.SubElement(Id, "OrgId")
            Othr = etree.SubElement(OrgId, "Othr")
            _Id = etree.SubElement(Othr, "Id")
            _Id.text = self._sanitize_communication(company.sepa_orgid_id)
            if company.sepa_orgid_issr:
                Issr = etree.SubElement(Othr, "Issr")
                Issr.text = self._sanitize_communication(company.sepa_orgid_issr)
            ret.append(Id)

        return ret

    def _get_InitgPty(self):
        InitgPty = etree.Element("InitgPty")
        InitgPty.extend(self._get_company_PartyIdentification32(org_id=True, postal_address=False))
        return InitgPty

    def _get_PmtTpInf(self):
        PmtTpInf = etree.Element("PmtTpInf")
        InstrPrty = etree.SubElement(PmtTpInf, "InstrPrty")
        InstrPrty.text = 'NORM'

        if not self.sct_generic:
            SvcLvl = etree.SubElement(PmtTpInf, "SvcLvl")
            Cd = etree.SubElement(SvcLvl, "Cd")
            Cd.text = 'SEPA'

        return PmtTpInf

    def _get_Dbtr(self):
        Dbtr = etree.Element("Dbtr")
        Dbtr.extend(self._get_company_PartyIdentification32(org_id=lambda: not self.sct_generic, postal_address=True))
        return Dbtr

    def _get_DbtrAcct(self):
        DbtrAcct = etree.Element("DbtrAcct")
        Id = etree.SubElement(DbtrAcct, "Id")
        IBAN = etree.SubElement(Id, "IBAN")
        IBAN.text = self.journal_id.bank_account_id.sanitized_acc_number
        Ccy = etree.SubElement(DbtrAcct, "Ccy")
        Ccy.text = self.journal_id.currency_id and self.journal_id.currency_id.name or self.journal_id.company_id.currency_id.name

        return DbtrAcct

    def _get_CdtTrfTxInf(self, PmtInfId, payment):
        CdtTrfTxInf = etree.Element("CdtTrfTxInf")
        PmtId = etree.SubElement(CdtTrfTxInf, "PmtId")
        InstrId = etree.SubElement(PmtId, "InstrId")
        InstrId.text = self._sanitize_communication(payment.name)
        EndToEndId = etree.SubElement(PmtId, "EndToEndId")
        EndToEndId.text = (PmtInfId.text + str(payment.id))[-30:]
        Amt = etree.SubElement(CdtTrfTxInf, "Amt")
        val_Ccy = payment.currency_id and payment.currency_id.name or payment.journal_id.company_id.currency_id.name
        val_InstdAmt = float_repr(float_round(payment.amount, 2), 2)
        max_digits = val_Ccy == 'EUR' and 11 or 15
        if len(re.sub('\.', '', val_InstdAmt)) > max_digits:
            raise ValidationError(_("The amount of the payment '%s' is too high. The maximum permitted is %s.") % (payment.name, str(9) * (max_digits - 3) + ".99"))
        InstdAmt = etree.SubElement(Amt, "InstdAmt", Ccy=val_Ccy)
        InstdAmt.text = val_InstdAmt
        CdtTrfTxInf.append(self._get_ChrgBr())
        CdtTrfTxInf.append(self._get_CdtrAgt(payment.partner_bank_account_id))
        Cdtr = etree.SubElement(CdtTrfTxInf, "Cdtr")
        Nm = etree.SubElement(Cdtr, "Nm")
        Nm.text = self._sanitize_communication((payment.partner_bank_account_id.acc_holder_name or payment.partner_id.name)[:70])
        if payment.payment_type == 'transfer':
            CdtTrfTxInf.append(self._get_CdtrAcct(payment.destination_journal_id.bank_account_id))
        else:
            CdtTrfTxInf.append(self._get_CdtrAcct(payment.partner_bank_account_id))
        val_RmtInf = self._get_RmtInf(payment)
        if val_RmtInf is not False:
            CdtTrfTxInf.append(val_RmtInf)
        return CdtTrfTxInf

    def _get_ChrgBr(self):
        ChrgBr = etree.Element("ChrgBr")
        ChrgBr.text = self.sct_generic and "SHAR" or "SLEV"
        return ChrgBr

    def _get_CdtrAgt(self, bank_account):
        CdtrAgt = etree.Element("CdtrAgt")
        FinInstnId = etree.SubElement(CdtrAgt, "FinInstnId")
        val_BIC = bank_account.bank_bic
        if val_BIC:
            BIC = etree.SubElement(FinInstnId, "BIC")
            BIC.text = val_BIC.replace(' ', '')
        elif not self.sct_generic:
            raise UserError(_("There is no Bank Identifier Code recorded for bank account '%s'") % bank_account.acc_number)

        return CdtrAgt

    def _get_CdtrAcct(self, bank_account):
        if not self.sct_generic and (not bank_account.acc_type or not bank_account.acc_type == 'iban'):
            raise UserError(_("The account %s, linked to partner '%s', is not of type IBAN.\nA valid IBAN account is required to use SEPA features.") % (bank_account.acc_number, bank_account.partner_id))

        CdtrAcct = etree.Element("CdtrAcct")
        Id = etree.SubElement(CdtrAcct, "Id")
        if self.sct_generic and bank_account.acc_type != 'iban':
            Othr = etree.SubElement(Id, "Othr")
            _Id = etree.SubElement(Othr, "Id")
            _Id.text = bank_account.acc_number
        else:
            IBAN = etree.SubElement(Id, "IBAN")
            IBAN.text = bank_account.sanitized_acc_number

        return CdtrAcct

    def _get_RmtInf(self, payment):
        if not payment.communication:
            return False
        RmtInf = etree.Element("RmtInf")
        Ustrd = etree.SubElement(RmtInf, "Ustrd")
        Ustrd.text = self._sanitize_communication(payment.communication)
        return RmtInf
