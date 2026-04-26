from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from doctors.models import Doctor
from appointments.models import Consultation
from core.models import Patient

# PharmaVendor model removed. Using inventory.Vendor.

class MedicineCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Medicine Categories"

    def __str__(self):
        return self.name

class Medicine(models.Model):
    SCHEDULE_CHOICES = [
        ('H', 'Schedule H'),
        ('H1', 'Schedule H1'),
        ('X', 'Schedule X'),
        ('OTC', 'Over the Counter'),
    ]
    
    category = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey('inventory.Vendor', on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred Vendor")
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, help_text="Generic name of the drug")
    manufacturer = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=100, help_text="Tablet, Syrup, Injection, etc.")
    schedule_type = models.CharField(max_length=5, choices=SCHEDULE_CHOICES, default='OTC', help_text="Drug Schedule Classification")
    reorder_level = models.PositiveIntegerField(default=10, help_text="Minimum stock level before reordering")
    
    def __str__(self):
        return f"{self.name} ({self.schedule_type})"

class Batch(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    vendor = models.ForeignKey('inventory.Vendor', on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(default=0)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Purchase price per unit")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price (MRP) per unit")
    received_date = models.DateField(default=timezone.now)
    stock_entry = models.ForeignKey('StockEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')

    def is_expired(self):
        return self.expiry_date <= timezone.now().date()
        
    def __str__(self):
        return f"{self.medicine.name} - {self.batch_number} (Exp: {self.expiry_date})"

class Sale(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    patient_name = models.CharField(max_length=200, blank=True, help_text="Patient Name (if not registered)")
    # Optional link to registered patient if you have a Patient model, user didn't specify one in requirements so keeping it simple for POS
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, help_text="Prescribing Doctor")
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_sales')
    admission = models.ForeignKey('admissions.Admission', on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_requests', help_text="Linked IPD Admission")
    date = models.DateTimeField(default=timezone.now)
    invoice = models.OneToOneField('billing.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='pharmacy_sale')
    status = models.CharField(max_length=20, default='completed') # pending, completed, cancelled

    def __str__(self):
        return f"Sale #{self.id} on {self.date.strftime('%Y-%m-%d')} ({self.status})"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Deduct stock on save
        if not self.pk: # Only on create
            self.batch.quantity -= self.quantity
            self.batch.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.batch.medicine.name}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    vendor = models.ForeignKey('inventory.Vendor', on_delete=models.CASCADE, related_name='purchase_orders')
    date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Estimated Total")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"PO #{self.id} - {self.vendor.name} ({self.status})"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    unit_price_expected = models.DecimalField(max_digits=10, decimal_places=2, help_text="Estimated Purchase Price")
    
    def __str__(self):
        return f"{self.quantity_requested} x {self.medicine.name}"

class StockEntry(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_entries')
    vendor = models.ForeignKey('inventory.Vendor', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    vendor_invoice_number = models.CharField(max_length=100, blank=True)
    vendor_invoice_date = models.DateField(null=True, blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Stock Entries"

    def __str__(self):
        return f"GRN #{self.id} - {self.vendor.name} on {self.date}"

# Update Batch to link to StockEntry (Monkey patch or just add field if Batch was defined above?)
# Batch is defined above. We need to add the field to the Batch class definition.

class MedicineReturn(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateTimeField(default=timezone.now)
    total_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reason = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Return for Sale #{self.sale.id} on {self.return_date.date()}"

class MedicineReturnItem(models.Model):
    medicine_return = models.ForeignKey(MedicineReturn, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.CASCADE)
    quantity_returned = models.PositiveIntegerField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_restocked = models.BooleanField(default=True, help_text="If true, quantity is added back to batch")

    def save(self, *args, **kwargs):
        if not self.pk and self.is_restocked:
            # Add stock back to batch
            self.sale_item.batch.quantity += self.quantity_returned
            self.sale_item.batch.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ret: {self.quantity_returned} x {self.sale_item.batch.medicine.name}"
