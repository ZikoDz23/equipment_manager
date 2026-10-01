{
    'name': 'Equipment Management',
    'version': '19.0.0.1',
    'category': 'Human Resources/Equipment',
    'summary': 'Manage company equipment assigned to employees',
    'description': """
Equipment Management
====================
The module manages company equipment assigned to employees.
Supports equipment registration, assignment, return, current availability, assignment history, search filters, groupings, access rights.
    """,
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/equipment_sequence.xml',
        'views/hr_employee_views.xml',
        'views/equipment_category_views.xml',
        'views/equipment_item_views.xml',
        'views/equipment_assignment_views.xml',
        'wizard/equipment_assignment_wizard_views.xml',
        'wizard/equipment_return_wizard_views.xml',
        'report/asset_handover_report.xml',
        'views/equipment_menus.xml',
        
    ],
    'author': 'Namane Ahmed Zakaria',
    'support': 'ahmedzakaria.namane@gmail.com',
    'demo': [
        'demo/equipment_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
