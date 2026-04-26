import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from doctors.models import Doctor, Department

added_doctor_names = [
    "Dr. J.R.D. Raja",
    "Dr. B. Kannan",
    "Dr. M. Gayathri",
    "Dr. P. Aruneswari",
    "Dr. M. Selvaraj",
    "Dr. Venthamarai T.",
    "Dr. T. Venthamarai",
    "Dr. Shanmuga Priya R.",
    "Dr. K. R. Jayashree",
    "Dr. Gopi S.",
    "Dr. Satish",
    "Dr. R. Mageshwaran"
]

print("--- Removing Added Doctors ---")
for name in added_doctor_names:
    try:
        doc = Doctor.objects.get(name=name)
        doc.delete()
        print(f"Removed: {name}")
    except Doctor.DoesNotExist:
        print(f"Skipped (Not Found): {name}")

print("\n--- Cleaning up Empty Departments ---")
# Only remove departments that have 0 doctors
for dept in Department.objects.annotate(doc_count=django.db.models.Count('doctors')).filter(doc_count=0):
    # Keep some core departments if they are useful, but here we'll clean up
    print(f"Removing empty department: {dept.name}")
    dept.delete()
