from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class EquipmentAssignment(models.Model):
    _name = 'equipment.assignment'
    _description = 'Equipment Assignment'

    equipment_id = fields.Many2one('equipment.item', string="Equipment", required=True, index=True, ondelete='restrict')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, index=True, ondelete='restrict')
    assigned_at = fields.Datetime(string="Assigned At", required=True, index=True, default=fields.Datetime.now)
    returned_at = fields.Datetime(string="Returned At", index=True)
    assigned_by = fields.Many2one('res.users', string="Assigned By", required=True, readonly=True, default=lambda self: self.env.user)
    returned_by = fields.Many2one('res.users', string="Returned By", readonly=True)
    condition_on_assignment = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged')
    ], string="Condition on Assignment", required=True, default='good')
    condition_on_return = fields.Selection([
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged')
    ], string="Condition on Return")
    return_status = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Under Maintenance'),
        ('lost', 'Lost'),
        ('retired', 'Retired')
    ], string="Return Status", default='available')
    notes = fields.Text(string="Notes")
    
    state = fields.Selection([
        ('active', 'Active'),
        ('returned', 'Returned')
    ], string="State", compute='_compute_state', store=True, index=True)

    @api.depends('returned_at')
    def _compute_state(self):
        for record in self:
            record.state = 'returned' if record.returned_at else 'active'

    @api.constrains('assigned_at', 'returned_at')
    def _check_dates(self):
        for record in self:
            if record.returned_at and record.returned_at < record.assigned_at:
                raise ValidationError(_("Return date cannot be earlier than assignment date."))

    @api.constrains('state', 'equipment_id')
    def _check_active_assignments(self):
        for record in self:
            if record.state == 'active':
                count = self.search_count([
                    ('equipment_id', '=', record.equipment_id.id),
                    ('state', '=', 'active'),
                    ('id', '!=', record.id)
                ])
                if count > 0:
                    raise ValidationError(_("Equipment cannot have multiple active assignments."))

    @api.constrains('returned_at', 'returned_by')
    def _check_return_data(self):
        for record in self:
            if record.returned_at and not record.returned_by:
                raise ValidationError(_("A returned assignment must contain returned_by."))
            if not record.returned_at and record.returned_by:
                raise ValidationError(_("An active assignment must not contain returned_by."))

    def init(self):
        super().init()
        # Create a PostgreSQL partial unique index to enforce one active assignment per equipment item
        self.env.cr.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS equipment_one_active_assignment
            ON {self._table} (equipment_id)
            WHERE returned_at IS NULL;
        """)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_returned(self):
        if not self.env.user.has_group('equipment_management.group_equipment_manager'):
            raise UserError(_("Normal users cannot delete assignments."))
