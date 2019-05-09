=======================================================
Odoo Mexico Localization for Invoice with Custom Number
=======================================================

This module extends the functionality of Mexican localization to support customs numbers when you generate the electronic invoice.

Usage
=====

To use this module, you need to:

- Create a customer invoice normally.
- Add the personalized number related to the customs information, separated by commas, 
  if there are several numbers for each line of the invoice associated with a product.

  For example, given the number of petition **16  52  3XXX  8000988**.

  The number of the corresponding request to import the good must be registered, which is integrated from left to right in the following way:

  Last 2 digits of the validation year followed by two spaces, 2 digits of the customs office followed by two spaces, 4 digits of the number of the patent followed by two spaces, 
  1 digit corresponding to the last digit of the current year, except that it is of a consolidated motion, initiated in the immediately preceding year or of the original motion 
  for a rectification, followed by 6 digits of the progressive numbering by customs.

  +------------+------------+---------+-----------+--------+------------+-----------------------+
  | Validation |            | Customs |           | Patent |            | Exercise and Quantity |
  +============+============+=========+===========+========+============+=======================+
  |     16     | Two Spaces |   52    | Two Space |  3XXX  | Two Spaces |       8000988         |
  +------------+------------+---------+-----------+--------+------------+-----------------------+

  With the previous value in the patent of our petition. These values must coincide with the SAT catalog in such a way that:

  * Validation: The year of validation. The value of positions one and two must be smaller or same as the last two digits of the year of the current date and must be greater or same as the last two digits of the year of the current date minus ten.

  * Customs: Code of customs clearance agent. Positions five and six must correspond to a key from the catalog of Customs (catCFDI: c_Aduana)

  * Patent: Positions nine through twelve must correspond to a patent number of the catalog of customs patents (catCFDI: c_PatenteAduanal)

  * Exercise: Last digit of the current year, unless it is of a consolidated motion, initiated in the immediately previous year or of the original motion for a rectification)

  * Quantity: The value of the last six digits must be between the minimum value 1 and the value maximum of consecutive numbers in the catalog quantity column catCFDI: c_NumPedimentoAduana that correspond to those used by customs in that year.

- Validate the invoice

For more information in the `SAT page <http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/cfdv33.pdf>`_. Page 70.
For more information in the SAT documentation
