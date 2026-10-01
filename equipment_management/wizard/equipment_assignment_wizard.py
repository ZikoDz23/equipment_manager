from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EquipmentAssignmentWizard(models.TransientModel):
    _name = 'equipment.assignment.wizard'
    _description = 'Equipment Assignment Wizard'

    equipment_id = fields.Many2one('equipment.item', string="Equipment", required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    assigned_at = fields.Datetime(string="Assigned At", required=True, default=fields.Datetime.now)
    condition_on_assignment = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged')
    ], string="Condition", required=True, default='good')
    notes = fields.Text(string="Notes")

    def action_confirm_assignment(self):
        self.ensure_one()
        equipment = self.equipment_id
        
        # Re-check availability
        if equipment.status != 'available':
            raise UserError(_("The equipment is no longer available."))
            
        if equipment.current_assignment_id:
            raise UserError(_("The equipment already has an active assignment."))

        # Create the assignment
        assignment = self.env['equipment.assignment'].sudo().create({
            'equipment_id': equipment.id,
            'employee_id': self.employee_id.id,
            'assigned_at': self.assigned_at,
            'assigned_by': self.env.user.id,
            'condition_on_assignment': self.condition_on_assignment,
            'notes': self.notes,
        })
        
        # Update equipment status
        equipment.write({
            'employee_id': self.employee_id.id,
            'current_assignment_id': assignment.id,
            'status': 'assigned',
        })
        
        return {'type': 'ir.actions.act_window_close'}
