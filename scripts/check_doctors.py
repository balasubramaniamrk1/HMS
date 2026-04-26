import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from doctors.models import Doctor, Department

print("--- Departments ---")
depts = Department.objects.all()
for d in depts:
    print(f"- {d.name} (Slug: {d.slug}, Doctors: {d.doctors.count()})")

print("\n--- Doctors ---")
doctors = Doctor.objects.all()
for d in doctors:
    print(f"- {d.name} ({d.department.name})")
