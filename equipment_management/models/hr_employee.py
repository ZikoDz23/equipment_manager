from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    equipment_item_ids = fields.One2many(
        'equipment.item', 'employee_id', string='Currently Assigned Equipment'
    )
    equipment_item_count = fields.Integer(
        string='Currently Assigned Equipment', compute='_compute_equipment_item_count'
    )

    @api.depends('equipment_item_ids')
    def _compute_equipment_item_count(self):
        counts = {
            employee.id: count
            for employee, count in self.env['equipment.item']._read_group(
                [
                    ('employee_id', 'in', self.ids),
                    ('status', '=', 'assigned'),
                ],
                ['employee_id'],
                ['__count'],
            )
        }
        for record in self:
            record.equipment_item_count = counts.get(record.id, 0)


    def action_open_equipment(self):
        self.ensure_one()
        return {
            'name': _('Currently Assigned Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.item',
            'view_mode': 'list,kanban,form',
            'domain': [('employee_id', '=', self.id), ('status', '=', 'assigned')],
            'context': {
                'search_default_status_assigned': 1,
            },
        }