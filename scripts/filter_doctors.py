import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from doctors.models import Doctor, Department

allowed_names = [
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

print("--- Filtering Doctors (Keeping only Docx list) ---")
all_doctors = Doctor.objects.all()
for doc in all_doctors:
    if doc.name not in allowed_names:
        print(f"Removing: {doc.name}")
        doc.delete()

print("\n--- Cleaning up Empty Departments ---")
for dept in Department.objects.annotate(doc_count=django.db.models.Count('doctors')).filter(doc_count=0):
    print(f"Removing empty department: {dept.name}")
    dept.delete()
