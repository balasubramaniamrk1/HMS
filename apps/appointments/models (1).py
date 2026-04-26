from django.db import models
from doctors.models import Doctor, Department
from core.models import Patient

class AppointmentRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    phone = models.CharField(max_length=15)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=50, help_text="e.g. Morning, Evening, or 10:00 AM")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.preferred_date}"

class Consultation(models.Model):
    appointment = models.OneToOneField(AppointmentRequest, on_delete=models.CASCADE, related_name='consultation')
    doctor_notes = models.TextField(help_text="Observations by the doctor")
    doctor_comments = models.TextField(help_text="Additional comments for the report", blank=True)
    diagnosis = models.TextField()
    prescription = models.TextField(help_text="Medicines and dosage (legacy text field)", blank=True)
    next_visit_date = models.DateField(null=True, blank=True)
    # Pharmacy Integration
    pharmacy_status = models.CharField(max_length=20, default='pending', 
                                     choices=[('pending', 'Pending'), ('partially_dispensed', 'Partially Dispensed'), ('dispensed', 'Dispensed'), ('skipped', 'Skipped')])
    
    consultation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation: {self.appointment.name} on {self.consultation_date.date()}"

class PrescriptionItem(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescription_items')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=50, help_text="e.g. 1-0-1")
    duration = models.CharField(max_length=50, help_text="e.g. 5 days")
    instruction = models.CharField(max_length=200, help_text="e.g. After food", blank=True)
    
    def __str__(self):
        return f"{self.medicine_name} ({self.dosage})"
