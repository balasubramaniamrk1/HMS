from .models import Doctor, Department

def grouped_doctors(request):
    """
    Context processor to provide doctors grouped by department for navigation.
    """
    departments = Department.objects.prefetch_related('doctors').all()
    
    # We only want departments that have doctors
    depts_with_doctors = [
        dept for dept in departments if dept.doctors.exists()
    ]

    return {
        'nav_departments': depts_with_doctors,
        'all_doctors': Doctor.objects.all(),
        'featured_doctors': Doctor.objects.filter(is_featured=True)
    }
