class EmployeeCategory(models.Model):

    _name = "hr.employee.category"
    _description = "Employee Category"

    name = fields.Char(string="Employee Tag", required=True)
    color = fields.Integer(string='Color Index')
   

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]