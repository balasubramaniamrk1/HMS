from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Department(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='departments/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_icon_class(self):
        icon_map = {
            'Cardiology': 'fas fa-heartbeat',
            'Cardialogy': 'fas fa-heartbeat',
            'Urology': 'fas fa-water',
            'Gynecologist': 'fas fa-female',
            'Gynecology': 'fas fa-female',
            'Orthopedics': 'fas fa-bone',
            'General Medicine': 'fas fa-stethoscope',
            'Plastic Surgery': 'fas fa-magic',
            'General Surgery': 'fas fa-hand-holding-medical',
            'ENT': 'fas fa-ear-listen',
            'Paediatrics': 'fas fa-child',
            'Psychiatry': 'fas fa-brain',
            'Anaesthesia': 'fas fa-vial',
            'Administration': 'fas fa-user-tie',
        }
        return icon_map.get(self.name, 'fas fa-hospital')

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile', null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    qualifications = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200, help_text="Specific area of focus, e.g., 'Interventional Cardiology'")
    bio = models.TextField()
    experience_years = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_monogram(self):
        # Remove 'Dr.' or 'Dr ' from the name
        name_only = self.name.replace('Dr.', '').replace('Dr ', '').strip()
        parts = name_only.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "DR"
