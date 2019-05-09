Tax Cash Basis Entries at Payment Date
======================================

Allow to create the Journal Entries for Taxes at date of payment.
The following tests cases pretend to enlight you on what is expected of each
one according to Mexican requirements.

Case Multi-currency (both invoice & payment) Payment before Invoice
-------------------------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued yesterday in USD at a rate => 1MXN = 1 USD.
        Booked like:

            Receivable          1160                1160    USD
                Revenue                 1000       -1000    USD
                Taxes to Collect         160        -160    USD

        Payment issued two days ago in USD at a rate => 1MXN = 0.80 USD.
        Booked like:

            Bank                1450                1160    USD
                Receivable              1450       -1160    USD

        This Generates a Exchange Rate Difference.
        Booked like:

            Receivable           290                   0    USD
                Gain Exchange rate       290           0    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1250                1000    USD
                Tax Base Account        1250       -1000    USD
            Taxes to Collect     200                 160    USD
                Taxes to Paid            200        -160    USD

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 1250.00
            - Paid to SAT MXN 200.00
            - Have a difference of MXN 40.00 for Taxes to Collect that I would
              later have to issue as a Loss in Exchange Rate Difference

            Loss Exchange rate    40                   0    USD
                Taxes to Collect          40           0    USD


Case Multi-currency (both invoice & payment) Payment after Invoice
------------------------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued two days ago in USD at a rate => 1MXN = 0.80 USD.
        Booked like:

            Receivable          1450                1160    USD
                Revenue                 1250       -1000    USD
                Taxes to Collect         200        -160    USD

        Payment issued today in USD at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Bank                 928                1160    USD
                Receivable               928       -1160    USD

        This Generates a Exchange Rate Difference.
        Booked like:

            Loss Exchange rate   522                   0    USD
                Receivable               522           0    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account     800                1000    USD
                Tax Base Account         800       -1000    USD
            Taxes to Collect     128                 160    USD
                Taxes to Paid            128        -160    USD

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 800.00
            - Paid to SAT MXN 128.00
            - Have a difference of MXN -72.00 for Taxes to Collect that I would
              later have to issue as a Gain in Exchange Rate Difference

            Taxes to Collect      72                   0    USD
                Gain Exchange rate        72           0    USD


Case Multi-currency (both invoice & payment) Payment same day than Invoice
--------------------------------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued two days ago in USD at a rate => 1MXN = 0.8 USD.
        Booked like:

            Receivable          1450                1160    USD
                Revenue                 1250       -1000    USD
                Taxes to Collect         200        -160    USD

        Payment issued two days ago in USD at a rate => 1 MXN = 0.8 USD.
        Booked like:

            Bank                1450                1160    USD
                Receivable              1450       -1160    USD

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1250                1000    USD
                Tax Base Account        1250       -1000    USD
            Taxes to Collect     200                 160    USD
                Taxes to Paid            200        -160    USD

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 1250.00
            - Paid to SAT MXN 200.00
            - Have no difference for Taxes to Collect


Case Invoiced Yesterday (MXN) Payment Two Days Ago (USD)
--------------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued yesterday in MXN at a rate => 1MXN = 1 USD.
        Booked like:

            Receivable          1160                   -      -
                Revenue                 1000           -      -
                Taxes to Collect         160           -      -

        Payment issued two days ago in USD at a rate => 1 MXN = 0.80 USD.
        Booked like:

            Bank                1160                 928    USD
                Receivable              1160        -928    USD

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1000                   0      -
                Tax Base Account        1000           0      -
            Taxes to Collect     160                   0      -
                Taxes to Paid            160           0      -

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case):
              * Tax Base Account MXN 1000.00
            - Paid to SAT MXN 160.00
            - Have no difference for Taxes to Collect


Case Invoiced Yesterday (USD) Payment Today (MXN)
-------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued yesterday in USD at a rate => 1MXN = 1 USD.
        Booked like:

            Receivable          1160                1160    USD
                Revenue                 1000       -1000    USD
                Taxes to Collect         160        -160    USD

        Payment issued today in MXN at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Bank                 928                   -      -
                Receivable               928           -      -

        This Generates a Exchange Rate Difference.
        Booked like:

            Loss Exchange rate   232                 232    USD
                Receivable               232        -232    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account     800                   0    USD
                Tax Base Account         800           0    USD
            Taxes to Collect     128                   0    USD  # (I'd expect the same value as in the invoice for amount_currency in tax: 160 USD) 
                Taxes to Paid            128           0    USD

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 800.00
            - Paid to SAT MXN 128.00
            - Have a difference of MXN -32.00 for Taxes to Collect that I would
              later have to issue as a Gain in Exchange Rate Difference

            Taxes to Collect      32                   0    USD
                Gain Exchange rate        32           0    USD


Case Invoiced Yesterday (MXN) Payment Today (MXN)
-------------------------------------------------

        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued yesterday in MXN at a rate => 1MXN = 1 USD.
        Booked like:

            Receivable          1160                   -      -
                Revenue                 1000           -      -
                Taxes to Collect         160           -      -

        Payment issued today in MXN at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Bank                1160                   -      -
                Receivable              1160           -      -

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1000                   -      -
                Tax Base Account        1000           -      -
            Taxes to Collect     160                   -      -
                Taxes to Paid            160           -      -

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 1000.00
            - Paid to SAT MXN 160.00
            - Have no difference for Taxes to Collect


Case Multi-currency (both invoice & payment) Payment before Invoice (Supplier)
------------------------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued yesterday in USD at a rate => 1MXN = 1 USD.
        Booked like:

            Expenses            1000                1000    USD
            Unpaid Taxes         160                 160    USD

                Payable                 1160       -1160    USD

        Payment issued two days ago in USD at a rate => 1MXN = 0.80 USD.
        Booked like:

            Payable             1450                1160    USD
                Bank                    1450       -1160    USD

        This Generates a Exchange Rate Difference.
        Booked like:

            Loss Exchange rate   290                   0    USD
                Payable                  290           0    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1250                1000    USD
                Tax Base Account        1250       -1000    USD
            Creditable Tax       200                 160    USD
                Unpaid Taxes             200        -160    USD

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 1250.00
            - Creditable Tax MXN 200.00
            - Have a difference of MXN -40.00 for Unpaid Taxes that I would
              later have to issue as a Loss in Exchange Rate Difference

            Unpaid Taxes          40                   0    USD
                Gain Exchange rate        40           0    USD


Case Multi-currency (both invoice & payment) Payment after Invoice (Supplier)
-----------------------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued two days ago in USD at a rate => 1MXN = 0.80 USD.
        Booked like:

            Expenses            1250                1000    USD
            Unpaid Taxes         200                 160    USD

                Payable                 1450       -1160    USD

        Payment issued today in USD at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Payable              928                1160    USD
                Bank                     928       -1160    USD

        This Generates a Exchange Rate Difference.
        Booked like:

            Payable              522                   0    USD
                Gain Exchange rate       522           0    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account     800                1000    USD
                Tax Base Account         800       -1000    USD
            Creditable Tax       128                 160    USD
                Unpaid Taxes             128        -160    USD

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 800.00
            - Creditable Tax MXN 128.00
            - Have a difference of MXN 72.00 for Unpaid Taxes that I would
              later have to issue as a Loss in Exchange Rate Difference

            Loss Exchange rate    72                   0    USD
                Unpaid Taxes              72           0    USD


Case Multi-currency (both invoice & payment) Payment same day than Invoice (Supplier)
-------------------------------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued two days ago in USD at a rate => 1MXN = 0.8 USD.
        Booked like:

            Expenses            1250                1000    USD
            Unpaid Taxes         200                 160    USD

                Payable                 1450       -1160    USD

        Payment issued two days ago in USD at a rate => 1 MXN = 0.8 USD.
        Booked like:

            Payable             1450                1160    USD
                Bank                    1450       -1160    USD

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1250                1000    USD
                Tax Base Account        1250       -1000    USD
            Creditable Tax       200                 160    USD
                Unpaid Taxes             200        -160    USD

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 1250.00
            - Creditable Tax MXN 200.00
            - Have no difference for Unpaid Taxes


Case Invoiced Yesterday (MXN) Payment Two Days Ago (USD) (Supplier)
-------------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued yesterday in MXN at a rate => 1MXN = 1 USD.
        Booked like:

            Expenses            1000                   -      -
            Unpaid Taxes         160                   -      -

                Payable                 1160           -      -

        Payment issued two days ago in USD at a rate => 1 MXN = 0.80 USD.
        Booked like:

            Payable             1160                 928    USD
                Bank                    1160        -928    USD

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1000                   0      -
                Tax Base Account        1000           0      -
            Creditable Tax       160                   0      -
                Unpaid Taxes             160           0      -

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 1000.00
            - Creditable Tax MXN 160.00
            - Have no difference for Unpaid Taxes


Case Invoiced Yesterday (USD) Payment Today (MXN) (Supplier)
------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued yesterday in USD at a rate => 1MXN = 1 USD.
        Booked like:

            Expenses            1000                1000    USD
            Unpaid Taxes         160                 160    USD

                Payable                 1160       -1160    USD

        Payment issued today in MXN at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Payable              928                   -      -
                Bank                     928           -      -

        This Generates a Exchange Rate Difference.
        Booked like:

            Payable              232                 232    USD
                Gain Exchange rate       522        -232    USD

        And a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account     800                   0    USD
                Tax Base Account         800           0    USD
            Creditable Tax       128                   0    USD  # (I'd expect the same value as in the invoice for amount_currency in tax: 160 USD) 
                Unpaid Taxes             128           0    USD

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 800.00
            - Creditable Tax MXN 128.00
            - Have a difference of MXN 32.00 for Unpaid Taxes that I would
              later have to issue as a Loss in Exchange Rate Difference

            Loss Exchange rate    32                   0    USD
                Unpaid Taxes              32           0    USD


Case Invoiced Yesterday (MXN) Payment Today (MXN) (Supplier)
------------------------------------------------------------

        Test to validate tax effectively Payable

        My company currency is MXN.

        Invoice issued yesterday in MXN at a rate => 1MXN = 1 USD.
        Booked like:

            Expenses            1000                   -      -
            Unpaid Taxes         160                   -      -

                Payable                 1160           -      -

        Payment issued today in MXN at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Payable             1160                   -      -
                Bank                    1160           -      -

        This does not generates any Exchange Rate Difference.

        But a Tax Cash Basis Entry is generated.
        Booked like:

            Tax Base Account    1000                   -      -
                Tax Base Account        1000           -      -
            Creditable Tax       160                   -      -
                Unpaid Taxes             160           -      -

        What I expect from here:
            - Base to report to DIOT: Tax Base Account MXN 1000.00
            - Creditable Tax MXN 160.00
            - Have no difference for Unpaid Taxes


Case Invoiced Yesterday (MXN) Credit Note Today (MXN) (Customer)
----------------------------------------------------------------
        Test to validate tax effectively receivable

        My company currency is MXN.

        Invoice issued two days ago in USD at a rate => 1MXN = 0.80 USD.
        Booked like:

            Receivable          1450                1160    USD
                Revenue                 1250       -1000    USD
                Taxes to Collect         200        -160    USD

        Credit Note issued today in USD at a rate => 1 MXN = 1.25 USD.
        Booked like:

            Revenue              800                1000    USD
            Taxes to Collect     128                 160    USD

                Receivable               928       -1160    USD

        This Generates a Exchange Rate Difference.
        Booked like:

            Loss Exchange rate   522                   0    USD
                Receivable               522           0    USD

        And two Tax Cash Basis Entry are generated.
        Booked like:

            Tax Base Account     800                1000    USD
                Tax Base Account         800       -1000    USD
            Taxes to Collect     128                 160    USD
                Taxes to Paid            128        -160    USD

            Tax Base Account     800                1000    USD
                Tax Base Account         800       -1000    USD
            Taxes to Paid        128                 160    USD
                Taxes to Collect         128        -160    USD

        What I expect from here:
            - Base to report to DIOT if it would be the case (not in this case): 
              * Tax Base Account MXN 800.00 and MXN -800.00
            - Paid to SAT MXN 0.00
            - Have a difference of MXN -72.00 for Taxes to Collect that I would
              later have to issue as a Gain in Exchange Rate Difference

            Taxes to Collect      72                   0    USD
                Gain Exchange rate        72           0    USD

Credits
=======

**Contributors**

* Nhomar Hernandez <nhomar@vauxoo.com> (Planner/Auditor)
* Luis Torres <luis_t@vauxoo.com> (Auditor)
* Humberto Arocha <luis_t@vauxoo.com> (Planner/Developer)
