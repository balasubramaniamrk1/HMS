import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from doctors.models import Doctor, Department

def seed_doctors():
    data = [
        {
            "name": "Dr. J.R.D. Raja",
            "qualifications": "MCh (Plastic Surgery)",
            "specialization": "Hand Surgery, Burn Care, Diabetic Foot",
            "department": "Plastic Surgery",
            "experience": 12,
            "bio": "Expert in Plastic Surgery with focus on Hand Surgery and Burn Care."
        },
        {
            "name": "Dr. B. Kannan",
            "qualifications": "DM (Cardiology)",
            "specialization": "Angiography, Angioplasty",
            "department": "Cardiology",
            "experience": 10,
            "bio": "Experienced Cardiologist specializing in Angiography."
        },
        {
            "name": "Dr. M. Gayathri",
            "qualifications": "MD (General Medicine)",
            "specialization": "Diabetic Care, Hypertension, Infection Control",
            "department": "General Medicine",
            "experience": 10,
            "bio": "Consultant in General Medicine."
        },
        {
            "name": "Dr. P. Aruneswari",
            "qualifications": "MS (General Surgery)",
            "specialization": "General Surgery",
            "department": "General Surgery",
            "experience": 5,
            "bio": "Specialist in General Surgery."
        },
        {
            "name": "Dr. M. Selvaraj",
            "qualifications": "DLO",
            "specialization": "ENT",
            "department": "ENT",
            "experience": 14,
            "bio": "Experienced ENT specialist."
        },
        {
            "name": "Dr. Venthamarai T.",
            "qualifications": "MBBS, DGO",
            "specialization": "Gynecology",
            "department": "Gynecology",
            "experience": 11,
            "bio": "Consultant Gynecologist."
        },
        {
            "name": "Dr. T. Venthamarai",
            "qualifications": "MBBS, DGO",
            "specialization": "Gynecology",
            "department": "Gynecology",
            "experience": 11,
            "bio": "Consultant Gynecologist."
        },
        {
            "name": "Dr. Shanmuga Priya R.",
            "qualifications": "MBBS, DCH",
            "specialization": "Intensive Care",
            "department": "Paediatrics",
            "experience": 7,
            "bio": "Paediatrician with focus on Intensive Care."
        },
        {
            "name": "Dr. K. R. Jayashree",
            "qualifications": "MD (Paediatrics)",
            "specialization": "Newborn Care",
            "department": "Paediatrics",
            "experience": 7,
            "bio": "Specialist in Newborn Care."
        },
        {
            "name": "Dr. Gopi S.",
            "qualifications": "MBBS, DPM",
            "specialization": "Anaesthesia Team",
            "department": "Psychiatry",
            "experience": 10,
            "bio": "Experienced in Psychological Medicine and Anaesthesia Support."
        },
        {
            "name": "Dr. Satish",
            "qualifications": "MBBS, MD (Anaesthesia)",
            "specialization": "Intensive Care",
            "department": "Anaesthesia",
            "experience": 15,
            "bio": "Specialist in Anaesthesia and Intensive Care."
        },
        {
            "name": "Dr. R. Mageshwaran",
            "qualifications": "MBBS, MD (Anaesthesia)",
            "specialization": "Anaesthesia",
            "department": "Anaesthesia",
            "experience": 12,
            "bio": "Consultant Anaesthetist."
        }
    ]

    for item in data:
        dept, _ = Department.objects.get_or_create(
            name=item["department"],
            defaults={"description": f"{item['department']} department"}
        )
        
        doctor, created = Doctor.objects.get_or_create(
            name=item["name"],
            defaults={
                "department": dept,
                "qualifications": item["qualifications"],
                "specialization": item["specialization"],
                "bio": item["bio"],
                "experience_years": item["experience"],
                "is_featured": True
            }
        )
        if created:
            print(f"Created doctor: {doctor.name}")
        else:
            print(f"Doctor already exists: {doctor.name}")

if __name__ == "__main__":
    seed_doctors()
