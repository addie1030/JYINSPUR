import odoo.tests
# @odoo.tests.common.at_install(False)
# @odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_01_ui(self):
        self.phantom_js("/", "odoo.__DEBUG__.services['web_tour.tour'].run('activity_creation')", "odoo.__DEBUG__.services['web_tour.tour'].tours.activity_creation.ready", login='admin')

    def test_02_ui(self):
        self.phantom_js("/", "odoo.__DEBUG__.services['web_tour.tour'].run('test_screen_navigation')", "odoo.__DEBUG__.services['web_tour.tour'].tours.test_screen_navigation.ready", login='admin')
