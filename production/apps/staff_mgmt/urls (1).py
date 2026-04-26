from django.urls import path
from . import views, views_admin

urlpatterns = [
    # Staff Dashboard
    path('dashboard/', views.staff_dashboard, name='staff_attendance'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('reports/attendance/', views.attendance_report, name='attendance_report'),

    # Hospital Admin Dashboard
    path('admin/', views_admin.admin_dashboard, name='admin_dashboard'),
    
    # Staff Mgmt (Admin)
    path('admin/staff/', views_admin.staff_list, name='staff_list'),
    path('admin/staff/add/', views_admin.staff_create, name='staff_create'),
    path('admin/staff/<int:pk>/edit/', views_admin.staff_edit, name='staff_edit'),
    
    # Doctor Mgmt (Admin)
    path('admin/doctors/', views_admin.doctor_list, name='doctor_list'),
    path('admin/doctors/add/', views_admin.doctor_create, name='doctor_create'),
    
    # Operations
    path('admin/departments/', views_admin.department_list, name='department_list'),
    path('admin/shifts/', views_admin.shift_list, name='shift_list'),
    path('admin/attendance/', views_admin.attendance_list, name='admin_attendance_list'),
    
    # Gallery (Admin)
    path('admin/gallery/', views_admin.gallery_list, name='gallery_list'),
    path('admin/gallery/upload/', views_admin.gallery_upload, name='gallery_upload'),
    path('admin/gallery/<int:pk>/delete/', views_admin.gallery_delete, name='gallery_delete'),
]
