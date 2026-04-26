from django.urls import reverse

def role_based_navigation(request):
    """
    Context processor to provide role-based navigation menus avoiding complex template logic.
    """
    user = request.user
    sidebar_menu = []
    
    if not user.is_authenticated:
        return {'sidebar_menu': []}

    # Helpers
    def has_group(group_names):
        if user.is_superuser:
            return True
        groups = [g.strip() for g in group_names.split(',')]
        return user.groups.filter(name__in=groups).exists()

    # --- Common Links ---
    sidebar_menu.append({
        'label': 'Dashboard',
        'url': reverse('unified_dashboard'), # Ensure this URL name exists or fallback to home
        'icon': 'fas fa-columns'
    })

    # --- Role Specific Links ---

    # Doctors
    if has_group("Doctors"):
        sidebar_menu.append({'label': 'Doctor Console', 'url': reverse('doctor_console'), 'icon': 'fas fa-user-md'})
        sidebar_menu.append({'label': 'Reports', 'url': reverse('reports_dashboard'), 'icon': 'fas fa-file-medical-alt'})

    # Billing
    if has_group("Billing,Hospital Admins"):
        sidebar_menu.append({'label': 'Billing', 'url': reverse('billing:dashboard'), 'icon': 'fas fa-file-invoice-dollar'})

    # Admissions
    if has_group("Doctors,Receptionist,Front Desk,Inventory Managers,Hospital Admins,Staff"):
        sidebar_menu.append({'label': 'Admissions (IPD)', 'url': reverse('admissions:dashboard'), 'icon': 'fas fa-procedures'})

    # Front Desk / Staff Dashboard
    if has_group("Receptionist,Front Desk,Staff,Hospital Admins,Doctors,Inventory Managers,Pharmacist"):
        sidebar_menu.append({'label': 'Staff Dashboard', 'url': reverse('staff_dashboard'), 'icon': 'fas fa-desktop'})
        sidebar_menu.append({'label': 'Book Appointment', 'url': reverse('book_appointment'), 'icon': 'fas fa-calendar-plus'})

    # Staff Attendance Portal (Requested URL: /staff/dashboard/)
    if has_group("Receptionist,Front Desk,Staff,Doctors,Inventory Managers,Pharmacist"):
        sidebar_menu.append({'label': 'My Attendance', 'url': reverse('staff_mgmt:staff_attendance'), 'icon': 'fas fa-clock'})

    # Pharmacy
    if has_group("Pharmacist,Inventory Managers"):
        sidebar_menu.append({'label': 'Pharmacy', 'url': reverse('pharmacy:dashboard'), 'icon': 'fas fa-pills'})
        sidebar_menu.append({'label': 'POS', 'url': reverse('pharmacy:pos'), 'icon': 'fas fa-cash-register'})
        sidebar_menu.append({'label': 'Purchase Orders', 'url': reverse('pharmacy:purchase_order_list'), 'icon': 'fas fa-file-contract'})

    # Inventory
    if has_group("Inventory Managers"):
        sidebar_menu.append({'label': 'Inventory', 'url': reverse('inventory_dashboard'), 'icon': 'fas fa-boxes'})
        sidebar_menu.append({'label': 'Equipment List', 'url': reverse('inventory_list'), 'icon': 'fas fa-list'})
        sidebar_menu.append({'label': 'Vendor List', 'url': reverse('vendor_list'), 'icon': 'fas fa-truck'})
        sidebar_menu.append({'label': 'AMC Contracts', 'url': reverse('amc_list'), 'icon': 'fas fa-file-signature'})

    # Admin
    if has_group("Hospital Admins"):
        sidebar_menu.append({'label': 'Admin Panel', 'url': reverse('staff_mgmt:admin_dashboard'), 'icon': 'fas fa-cogs'})
        sidebar_menu.append({'label': 'Departments', 'url': reverse('department_list'), 'icon': 'fas fa-building'})

    return {
        'sidebar_menu': sidebar_menu,
    }
