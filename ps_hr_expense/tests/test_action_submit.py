from odoo.tests import TransactionCase


class TestPsHrExpenseRequest(TransactionCase):
    """
    """

    def setUp(self):
        super(TestPsHrExpenseRequest, self).setUp()

    def test_action_submit(self):
        """
        ====================ps_hr_expense_request:Error=================
        """
        # rec = self.env['ps.hr.expense.request'].search([('name', '=', 'ER#000004')])
        # rec.action_submit()
        pass
