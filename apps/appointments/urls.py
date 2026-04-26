from django.urls import path
from . import views

urlpatterns = [
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    # Management
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('update-status/<int:pk>/<str:status>/', views.update_status, name='update_status'),
    path('doctor-console/', views.doctor_console, name='doctor_console'),
    path('consult/<int:pk>/', views.consultation_view, name='consultation'),
    path('reschedule/<int:pk>/', views.reschedule_appointment, name='reschedule_appointment'),
    path('cancel-doctor/<int:pk>/', views.cancel_appointment_doctor, name='cancel_appointment_doctor'),
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('consultation/<int:pk>/', views.consultation_detail_view, name='consultation_detail'),
    path('patient-history/<str:patient_id>/', views.patient_history_view, name='patient_history'),
    path('prescription/<int:consultation_id>/pdf/', views.download_prescription_pdf, name='download_prescription_pdf'),
]
