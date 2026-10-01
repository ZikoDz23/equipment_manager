from odoo import models, fields

class EquipmentCategory(models.Model):
    _name = 'equipment.category'
    _description = 'Equipment Category'
    
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True, index=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, index=True, default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'The code of the equipment category must be unique per company!')
    ]
