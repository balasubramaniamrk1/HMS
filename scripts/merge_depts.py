import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
django.setup()

from doctors.models import Doctor, Department

def merge_departments(old_name, new_name):
    try:
        old_dept = Department.objects.get(name=old_name)
        new_dept, _ = Department.objects.get_or_create(name=new_name)
        
        doctors = Doctor.objects.filter(department=old_dept)
        count = doctors.count()
        doctors.update(department=new_dept)
        
        print(f"Moved {count} doctors from '{old_name}' to '{new_name}'")
        
        # Delete old department if it has no doctors
        if old_dept.doctors.count() == 0:
            old_dept.delete()
            print(f"Deleted old department '{old_name}'")
    except Department.DoesNotExist:
        print(f"Department '{old_name}' does not exist, skipping.")

if __name__ == "__main__":
    merge_departments('Cardialogy', 'Cardiology')
    merge_departments('Gynecologist', 'Gynecology')
    # Also ensure slugs are consistent
    for dept in Department.objects.all():
        if dept.name == 'Cardiology' and dept.slug != 'cardiology':
            dept.slug = 'cardiology'
            dept.save()
        if dept.name == 'Gynecology' and dept.slug != 'gynecology':
            dept.slug = 'gynecology'
            dept.save()
