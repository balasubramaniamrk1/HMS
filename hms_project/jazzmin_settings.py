
# Jazzmin Settings
JAZZMIN_SETTINGS = {
    "site_title": "HealthPlus Admin",
    "site_header": "HealthPlus Administration",
    "site_brand": "HealthPlus HMS",
    "welcome_sign": "Welcome to HealthPlus Hospital Management",
    "copyright": "HealthPlus HMS Ltd",
    "search_model": ["appointments.AppointmentRequest", "doctors.Doctor"],
    
    # UI Customizer
    "show_ui_builder": False,
    
    "topmenu_links": [
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/", "new_window": True},
    ],
    
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "auth.user"}
    ],

    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["appointments", "doctors", "core", "auth"],

    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "doctors.Doctor": "fas fa-user-md",
        "doctors.Department": "fas fa-hospital",
        "appointments.AppointmentRequest": "fas fa-calendar-check",
        "appointments.Consultation": "fas fa-stethoscope",
        "core.HealthPackage": "fas fa-medkit",
        "core.ContactMessage": "fas fa-envelope",
        "core.CareerApplication": "fas fa-user-tie",
        "blog.Post": "fas fa-newspaper",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-info",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "theme": "slate",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
