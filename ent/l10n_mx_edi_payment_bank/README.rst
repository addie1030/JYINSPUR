Bank account used in the payment
================================

The CFDI document that is generated in each payment has the next attributes:

- RfcEmisorCtaOrd: Is the NIF of the entity from where was made the payment.
  If this entity is foreign must be used the generic value `XEXX010101000`.
- NomBancoOrdExt: Is the name of the entity from where was made the payment.
  If the entity is foreing this value must be established.
- CtaOrdenante: Is the account number that was used in the payment.o
- RfcEmisorCtaBen: Is the NIF of the company bank where was received the
  payment.
- CtaBeneficiario: Is the company bank account where was received the
  payment.

This attributes are optionals but by soma customers is required that all the
CFDIs documents with payment complement comes with this information.

When I need add that information?
----------------------------------

If the payment was made with some of the next payment methods this fields are
optionals:

+------+-------------------+
| Code | Name              |
+======+===================+
| 02   | Check             |
+------+-------------------+
| 03   | Transfer          |
+------+-------------------+
| 04   | Credit Card       |
+------+-------------------+
| 05   | Electronic Wallet |
+------+-------------------+
| 06   | Electronic Cash   |
+------+-------------------+
| 28   | Debit Card        |
+------+-------------------+
| 29   | Services Card     |
+------+-------------------+

How can I set the bank account in the payment?
----------------------------------------------

To this process is necessary create a new bank account in the partner.

Is important indicathe the country in the bank, remember that if is a
foreing institution the NIF is a generic.

If the payment is made from the Bank Statement:

  Was enabled a field in the statement line where could be set the bank
  account previously created or could be created in the bank statement.

    .. figure:: ../l10n_mx_edi_payment_bank/static/src/statement.png

If the payment is generated from a invoice or a list of invoices:

  Here also was enabled a field where could be set the bank account previously
  created.

    .. figure:: ../l10n_mx_edi_payment_bank/static/src/wizard.png

To the infortmation about the company accounts the bank is used the
account configured in the bank journals.
