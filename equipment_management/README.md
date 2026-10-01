# Equipment Management

This Odoo module manages company equipment, employee assignments, returns, availability, and assignment history.


## Business Need

The company currently tracks computers, phones, tools, and accessories through spreadsheets and emails. This makes it difficult to know who currently has an item, which equipment is available, and what happened during its assignment history. This module centralizes that information in Odoo and provides a controlled assign/return workflow, current availability, employee visibility, and historical tracking.

## Modeling Choices

- `equipment.category` stores reusable categories and company-specific category codes.
- `equipment.item` represents one physical item and stores its current operational snapshot: status, current employee, and current assignment.
- `equipment.assignment` stores historical and active assignment records, including dates, responsible users, conditions, resulting status, and notes.
- Assignment and return wizards are the controlled workflow boundary. Assignment history is read-only through normal model access.
- Current state is stored on `equipment.item` so common availability and employee queries do not need to scan the complete history.

## Assumptions

- Each equipment record represents one individually tracked physical item.
- Employees must already exist in Odoo HR and are linked through `hr.employee`.
- An item can have only one active assignment at a time. Returned assignments are retained as history.
- The item's current employee is stored on `equipment.item.employee_id`; `equipment.assignment` retains the assignment history.
- Serial numbers are optional but must be unique when provided.
- Maintenance is limited to equipment lifecycle statuses; the module does not provide separate maintenance orders or workflows.
- Stock movements, purchasing, accounting, depreciation, and procurement are outside the module's scope.
- Each equipment item is associated with a company, and record rules control multi-company visibility.
- Equipment is archived rather than deleted to preserve its history and references.

## Performance Considerations

- Frequently searched fields such as reference, serial number, category, company, employee, status, and assignment dates are indexed.
- A PostgreSQL partial unique index prevents more than one active assignment for the same equipment item.
- The current equipment snapshot avoids aggregating assignment history for normal list and employee views.
- Odoo list pagination, search domains, and groupings are used instead of loading the complete registry into memory.
- Counters are computed with grouped ORM queries rather than loading every related record. If assignment history grows substantially, these counters should still be benchmarked against stored counters.

## Quick Start

1. Add `sig_test` to the Odoo addons path.
2. Restart Odoo and update the Apps list.
3. Install or upgrade `equipment_management`.
4. Assign users to Equipment / User or Equipment / Manager.

## Main Features

- Equipment registry with categories, status, serial number, location, warranty, and notes.
- Guided assignment and return workflows.
- Printable Asset Handover Form PDF from an assignment record, with equipment details, handover condition, and employee/issuer signature fields.
- Current employee and assignment visibility.
- Assignment history.
- List, kanban, graph, pivot, filters, and groupings.
- Multi-company visibility rules.
- Equipment and assignment workflow tests.

## Assignment Workflow

1. Open an available equipment item and use **Assign** to select the employee and record the handover condition and notes.
2. Confirm the assignment. Odoo creates an assignment history record and updates the item's current status and employee.
3. Open the assignment record and choose **Print → Asset Handover Form**. Print the PDF for the employee and issuer to sign, then retain the signed copy according to company policy.
4. When the equipment is returned, use the return workflow to record its condition and resulting status.

## Test Command

```bash
odoo-bin -d <test_database> -i equipment_management --test-enable --test-tags /equipment_management
```
