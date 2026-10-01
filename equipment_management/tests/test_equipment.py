from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo import fields
from datetime import timedelta

class TestEquipment(TransactionCase):

    def setUp(self):
        super(TestEquipment, self).setUp()
        self.category = self.env['equipment.category'].create({
            'name': 'Test Category',
            'code': 'TEST',
        })
        self.employee1 = self.env['hr.employee'].create({'name': 'Employee 1'})
        self.employee2 = self.env['hr.employee'].create({'name': 'Employee 2'})
        
    def test_equipment_creation(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 1',
            'category_id': self.category.id,
        })
        self.assertEqual(equipment.status, 'available')
        self.assertTrue(equipment.reference.startswith('EQ/'))
        self.assertEqual(equipment.company_id, self.env.company)

    def test_asset_handover_report_is_bound_to_assignments(self):
        report = self.env.ref('equipment_management.action_report_asset_handover')

        self.assertEqual(report.model, 'equipment.assignment')
        self.assertEqual(report.binding_model_id.model, 'equipment.assignment')
        self.assertEqual(report.report_type, 'qweb-pdf')
        
    def test_assignment_workflow(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 2',
            'category_id': self.category.id,
        })
        
        wizard = self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
            'employee_id': self.employee1.id,
        })
        wizard.action_confirm_assignment()
        
        self.assertEqual(equipment.status, 'assigned')
        self.assertEqual(equipment.employee_id, self.employee1)
        self.assertTrue(equipment.current_assignment_id)
        self.assertEqual(equipment.assignment_count, 1)
        self.assertEqual(self.employee1.equipment_item_count, 1)
        self.assertEqual(self.employee2.equipment_item_count, 0)
        
        with self.assertRaises(UserError):
            wizard2 = self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
                'employee_id': self.employee2.id,
            })
            wizard2.action_confirm_assignment()

    def test_invalid_status_assignment(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 3',
            'category_id': self.category.id,
        })
        
        for status in ['retired', 'lost', 'maintenance']:
            equipment.status = status
            with self.assertRaises(UserError):
                wizard = self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
                    'employee_id': self.employee1.id,
                })
                wizard.action_confirm_assignment()
                
    def test_assigned_equipment_requires_return_before_status_change(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq Assigned Status',
            'category_id': self.category.id,
        })
        self.env['equipment.assignment.wizard'].with_context(
            default_equipment_id=equipment.id
        ).create({'employee_id': self.employee1.id}).action_confirm_assignment()

        for action_name in ('action_set_maintenance', 'action_mark_lost', 'action_retire'):
            with self.assertRaises(UserError):
                getattr(equipment, action_name)()

        self.assertEqual(equipment.status, 'assigned')
        self.assertEqual(equipment.employee_id, self.employee1)

    def test_return_workflow(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 4',
            'category_id': self.category.id,
        })
        wizard = self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
            'employee_id': self.employee1.id,
        })
        wizard.action_confirm_assignment()
        assignment = equipment.current_assignment_id
        
        return_wiz = self.env['equipment.return.wizard'].with_context(
            default_equipment_id=equipment.id,
            default_assignment_id=assignment.id
        ).create({
            'return_status': 'available',
        })
        return_wiz.action_confirm_return()
        
        self.assertTrue(assignment.returned_at)
        self.assertEqual(assignment.returned_by, self.env.user)
        self.assertFalse(equipment.employee_id)
        self.assertFalse(equipment.current_assignment_id)
        self.assertEqual(equipment.status, 'available')
        
        with self.assertRaises(UserError):
            return_wiz.action_confirm_return()

    def test_maintenance_return(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 5',
            'category_id': self.category.id,
        })
        self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
            'employee_id': self.employee1.id,
        }).action_confirm_assignment()
        
        return_wiz = self.env['equipment.return.wizard'].with_context(
            default_equipment_id=equipment.id,
            default_assignment_id=equipment.current_assignment_id.id
        ).create({
            'return_status': 'maintenance',
        })
        return_wiz.action_confirm_return()
        
        self.assertEqual(equipment.status, 'maintenance')

    def test_dates_validation(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 6',
            'category_id': self.category.id,
        })
        with self.assertRaises(ValidationError):
            equipment.write({
                'purchase_date': '2023-01-01',
                'warranty_expiration_date': '2022-01-01',
            })
            
        self.env['equipment.assignment.wizard'].with_context(default_equipment_id=equipment.id).create({
            'employee_id': self.employee1.id,
        }).action_confirm_assignment()
        assignment = equipment.current_assignment_id
        
        with self.assertRaises(ValidationError):
            assignment.write({
                'returned_at': assignment.assigned_at - timedelta(days=1),
                'returned_by': self.env.user.id
            })

    def test_database_uniqueness(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq 7',
            'category_id': self.category.id,
        })
        self.env['equipment.assignment'].create({
            'equipment_id': equipment.id,
            'employee_id': self.employee1.id,
            'assigned_at': fields.Datetime.now(),
        })
        with self.assertRaises(ValidationError):
            self.env['equipment.assignment'].create({
                'equipment_id': equipment.id,
                'employee_id': self.employee2.id,
                'assigned_at': fields.Datetime.now(),
            })

    def test_equipment_is_archived_instead_of_deleted(self):
        equipment = self.env['equipment.item'].create({
            'name': 'Test Eq Archive',
            'category_id': self.category.id,
        })
        with self.assertRaises(UserError):
            equipment.unlink()
