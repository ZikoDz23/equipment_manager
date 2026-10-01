from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EquipmentReturnWizard(models.TransientModel):
    _name = 'equipment.return.wizard'
    _description = 'Equipment Return Wizard'

    equipment_id = fields.Many2one('equipment.item', string="Equipment", required=True, readonly=True)
    assignment_id = fields.Many2one('equipment.assignment', string="Assignment", required=True, readonly=True)
    employee_id = fields.Many2one(related='assignment_id.employee_id', string="Employee", readonly=True)
    returned_at = fields.Datetime(string="Return Date/Time", required=True, default=fields.Datetime.now)
    condition_on_return = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged')
    ], string="Return Condition", required=True, default='good')
    return_status = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('retired', 'Retired')
    ], string="Resulting Status", required=True, default='available')
    notes = fields.Text(string="Notes")

    def action_confirm_return(self):
        self.ensure_one()
        assignment = self.assignment_id
        equipment = self.equipment_id
        
        # Re-check assignment active
        if assignment.state == 'returned':
            raise UserError(_("This assignment was already returned."))
            
        if equipment.current_assignment_id != assignment:
            raise UserError(_("The active assignment does not match."))

        # Update assignment
        assignment.sudo().write({
            'returned_at': self.returned_at,
            'returned_by': self.env.user.id,
            'condition_on_return': self.condition_on_return,
            'return_status': self.return_status,
            'notes': self.notes if self.notes else assignment.notes,
        })
        
        # Clear equipment status
        equipment.write({
            'employee_id': False,
            'current_assignment_id': False,
            'status': self.return_status,
        })
        
        return {'type': 'ir.actions.act_window_close'}
