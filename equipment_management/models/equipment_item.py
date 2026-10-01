from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class EquipmentItem(models.Model):
    _name = 'equipment.item'
    _description = 'Equipment Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Equipment Name", required=True, tracking=True)
    reference = fields.Char(string="Reference", required=True, readonly=True, copy=False, index=True, default=lambda self: _('New'))
    serial_number = fields.Char(string="Serial Number", index=True, tracking=True, copy=False)
    category_id = fields.Many2one('equipment.category', string="Category", required=True, index=True, ondelete='restrict', tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, index=True, default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string="Current Employee", readonly=True, index=True, tracking=True)
    current_assignment_id = fields.Many2one('equipment.assignment', string="Current Assignment", readonly=True, index=True)
    
    status = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('retired', 'Retired'),
    ], string="Status", required=True, index=True, tracking=True, default='available')
    
    location = fields.Char(string="Location", index=True)
    purchase_date = fields.Date(string="Purchase Date")
    warranty_expiration_date = fields.Date(string="Warranty Expiration Date")
    notes = fields.Text(string="Notes")
    
    assignment_ids = fields.One2many('equipment.assignment', 'equipment_id', string="Assignments")
    assignment_count = fields.Integer(string="Assignment Count", compute='_compute_assignment_count')
    
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'The reference of the equipment must be unique!')
    ]

    @api.ondelete(at_uninstall=False)
    def _unlink_forbidden(self):
        raise UserError(_("Equipment must be archived instead of deleted."))

    @api.constrains('purchase_date', 'warranty_expiration_date')
    def _check_dates(self):
        for record in self:
            if record.purchase_date and record.warranty_expiration_date and record.warranty_expiration_date < record.purchase_date:
                raise ValidationError(_("Warranty expiration cannot be earlier than purchase date."))
                
    @api.constrains('serial_number')
    def _check_serial_number(self):
        for record in self:
            if record.serial_number:
                domain = [
                    ('serial_number', '=', record.serial_number),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("The serial number must be unique!"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('equipment.item') or _('New')
        return super().create(vals_list)

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        counts = {
            equipment.id: count
            for equipment, count in self.env['equipment.assignment']._read_group(
                [('equipment_id', 'in', self.ids)],
                ['equipment_id'],
                ['__count'],
            )
        }
        for record in self:
            record.assignment_count = counts.get(record.id, 0)

    def action_assign(self):
        self.ensure_one()
        if self.status != 'available':
            raise UserError(_("Only available equipment can be assigned."))
        return {
            'name': _('Assign Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_equipment_id': self.id},
        }

    def action_return(self):
        self.ensure_one()
        if self.status != 'assigned':
            raise UserError(_("Only assigned equipment can be returned."))
        if not self.current_assignment_id:
            raise UserError(_("No active assignment found for this equipment."))
            
        return {
            'name': _('Return Equipment'),
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_equipment_id': self.id,
                'default_assignment_id': self.current_assignment_id.id,
            },
        }

    def action_set_available(self):
        self.ensure_one()
        if self.status != 'maintenance':
            raise UserError(_("Only equipment under maintenance can be manually set to available."))
        self.status = 'available'

    def action_set_maintenance(self):
        self.ensure_one()
        if self.status not in ('available', 'assigned'):
            raise UserError(_("Equipment cannot be placed under maintenance from its current status."))
        if self.status == 'assigned':
            raise UserError(_("Return the equipment before placing it under maintenance."))
        self.status = 'maintenance'

    def action_mark_lost(self):
        self.ensure_one()
        if self.status not in ('available', 'assigned'):
            raise UserError(_("Equipment cannot be marked as lost from its current status."))
        if self.status == 'assigned':
            raise UserError(_("Return the equipment before marking it as lost."))
        self.status = 'lost'

    def action_retire(self):
        self.ensure_one()
        if self.status == 'retired':
            raise UserError(_("Equipment is already retired."))
        if self.status == 'assigned':
            raise UserError(_("Return the equipment before retiring it."))
        self.status = 'retired'

    def action_view_assignments(self):
        self.ensure_one()
        return {
            'name': _('Assignments'),
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.assignment',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }
        
    @api.constrains('status', 'employee_id', 'current_assignment_id')
    def _check_status_consistency(self):
        for record in self:
            if record.status == 'assigned':
                if not record.employee_id:
                    raise ValidationError(_("An assigned equipment item must have a current employee."))
                if not record.current_assignment_id:
                    raise ValidationError(_("An assigned equipment item must have a current assignment."))
            elif record.status in ('available', 'maintenance', 'lost', 'retired'):
                if record.employee_id or record.current_assignment_id:
                    raise ValidationError(_("An available, lost, maintenance, or retired item must not have a current employee or current assignment."))
