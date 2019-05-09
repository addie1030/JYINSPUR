# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.tests


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_ui(self):
        self.phantom_js(
            "/",
            "odoo.__DEBUG__.services['web_tour.tour'].run('hr_contract_salary_tour', 'test')",
            "odoo.__DEBUG__.services['web_tour.tour'].tours.hr_contract_salary_tour.ready", login='admin',
            timeout=100)
