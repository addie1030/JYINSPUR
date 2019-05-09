External Trade Complement for the Mexican localization
=======================================================

This module adds the External Trade Complement to CFDI version 3.3, in which
was added the customs information of the products, it specifies the emitter
and receiver address, and also data related to export laws.

This complement is required for all invoices where goods are exported and the
landing code is "A1"

The following fields were added in order to comply with complement structure
defined by the SAT.

- In the invoice:

  - **Need external trade?**: This field is used to indicate that in the CFDI
    document that will be generated, must be added the external trade
    complement. By default take this value from the partner, but could be
    changed here if is one exception. If this field is actived, then will be
    showed the next fields:

  - **Certificate Source**: If the document to be generated is a
    Certificate of Origin, must be registered the certificate of
    origin folio or the fiscal folio in CFDI with which the issuance of the
    certificate of origin was paid. If this field is empty, indicate that
    this document not funge as Certificate of Origin.


    .. figure:: ../l10n_mx_edi_external_trade/static/src/InvoiceET.png

- In the product:

  - **Tariff Fraction**: This field is used to store the tariff fraction
    that corresponds to the product to be sold, this have loaded the SAT
    catalog "c_FraccionArancelaria_". If one record is not found is because
    only was loaded the current records.

  - **UMT Customs**: Field used to specify the key of the applicable unit
    of measure for the quantity expressed in the goods at customs. This
    unit of measure must correspond to the assigned Tariff Fraction in the
    product, as indicated in the SAT catalog.

  - **Weight**: If the *UMT Customs* is `KG`, here must be specific the weight
    of each product.


    .. figure:: ../l10n_mx_edi_external_trade/static/src/Product_CET.png

- In Unit of measurement

  - **Customs Code**: Code that corresponding to the unit of measurement in the
    SAT's catalog. This is the code that use the aduana to the products
    related. Link_


    .. figure:: ../l10n_mx_edi_external_trade/static/src/Code_Aduana.png

- In the invoice lines:

  - **Qty UMT**: It is the quantity expressed in the unit of measure of
    customs of the product.

    It will be used for the attribute "CantidadAduana" in each of the
    merchandise to sell, when the Code Customs of the product UMT is
    different to 99.

    This field is automatically filled in the invoice lines in the
    following cases:

    1. The product has the same value for UMT customs and UoM.
           In this case, Qty UMT is set to the same value of the quantity of
           products on the line.

    2. The code of the unit of measurement in UMT of the product is equal to 06 (kilo).
           In this case, Qty UMT will be equal to the weight defined in the
           product multiplied by the quantity of products being sold.

    In other cases, this value must be defined by the user, in each one of the
    lines.

  - **Unit Value UMT**: Represents the unit price of the merchandise in the
    Customs UMT. It is used to set the attribute "ValorUnitarioAduana" in
    each of the CFDI merchandise. It is transparent to the user.

  - **UMT Adduana**: This value by default is the same that is defined in the
    product of the line.


    .. figure:: ../l10n_mx_edi_external_trade/static/src/invoice_line_ET.png
      :width: 700pt

- In the partner:

  - **Need external trade?**: Field used to indicate if the customer needs
    his/her invoices with external complement. If the field is equal to True,
    then the add-on is added to the CFDIs for this client.


    .. figure:: ../l10n_mx_edi_external_trade/static/src/partnerET2.png

  - **Locality**: Field used to indicate the locality of the emitter and
    receiver in the CFDI

  - **Colony Code**: This field is used to store the emitter's code of the
    colony. It must be a value from the ones provided by the SAT's catalog.
    Note: This field only must be configured in the company address or in
    the partners that are used as branch address in multi-branch enviroments.
    c_colonia_

    .. figure:: ../l10n_mx_edi_external_trade/static/src/partnerET.png

- In the Company

  - **Number of Reliable Exporter**: Identification of the exporter
    according to the Article 22 of Annex 1 of the Free Trade Agreement with
    the European Association and to the Decision of the European Community,
    used to establish the attribute "NumeroExportadorConfiable" if the
    country of the customer belongs to the Union European

- In addition, the following models were added:

  - **Locality**:  model used to store the localities from Mexico provided
    by the SAT's catalog. Its fields are name, state, country and code.
    c_localidad_

In this version, the external trade complement does not support the Type of
Transfer Proof ('T'). For this reason, the nodes "Propietario" and
"MotivodeTraslado" are not specified in the External Trade Template. On the
other hand, the optional node "DescripcionesEspecificas" will not be added
in this version, since it needs fields that depend on the stock module.
They will be added in a later version.

.. _c_FraccionArancelaria: http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/c_FraccionArancelaria.xls 
.. _Link: http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/c_UnidadMedidaAduana.xls
.. _c_colonia: http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/c_Colonia.xls
.. _c_localidad: http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/c_Localidad.xls
