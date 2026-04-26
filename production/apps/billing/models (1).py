from django.db import models
from django.utils import timezone
from doctors.models import Doctor

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    patient_name = models.CharField(max_length=200, help_text="Patient Name")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    consultation = models.ForeignKey('appointments.Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    admission = models.ForeignKey('admissions.Admission', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Generic relation or just simple text for source?
    # For now, let's keep it simple. If it's from Pharmacy, we can link it via Sale (which will link here)
    # or we can add a 'source' field.
    source = models.CharField(max_length=50, default='pharmacy', help_text="pharmacy, consultation, lab, etc.")

    def __str__(self):
        return f"Invoice #{self.id} - {self.patient_name} - {self.status}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.line_total})"

class Payment(models.Model):
    PAYMENT_MODES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('insurance', 'Insurance'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='cash')
    transaction_id = models.CharField(max_length=100, blank=True, help_text="UPI Ref or Card Auth Code")
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.amount} via {self.mode}"
