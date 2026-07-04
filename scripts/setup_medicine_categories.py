import os, sys, django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()
from pharmacy.models import MedicineCategory
categories = ['Analgesics', 'Antibiotics', 'Antipyretics', 'Vitamins & Supplements', 'Cardiovascular', 'Respiratory', 'Dermatological', 'Gastrointestinal', 'Syrups & Suspensions', 'Injections']
for cat in categories:
    MedicineCategory.objects.get_or_create(name=cat)
print("Categories added successfully.")
