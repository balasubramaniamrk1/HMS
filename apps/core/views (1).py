from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from doctors.models import Department, Doctor
from .models import HealthPackage, ContactMessage, GalleryImage, CareerApplication
from apps.core.validators import validate_phone_number
from django.core.exceptions import ValidationError

@login_required
def gallery(request):
    images = GalleryImage.objects.all()
    return render(request, 'core/gallery.html', {'images': images})

def role_based_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect('admin_dashboard')
    elif user.groups.filter(name='Hospital Admins').exists():
        return redirect('admin_dashboard')
    elif user.groups.filter(name='Inventory Managers').exists():
        return redirect('inventory_list')
    elif user.groups.filter(name='Doctors').exists():
        return redirect('doctor_console')
    elif user.groups.filter(name='Receptionist').exists():
        return redirect('staff_dashboard')
    elif user.groups.filter(name='Staff').exists():
        return redirect('staff_attendance')
    else:
        return redirect('home')

def home(request):
    departments = Department.objects.all()[:4] # Featured departments
    doctors = Doctor.objects.filter(is_featured=True)[:4]
    context = {
        'departments': departments,
        'doctors': doctors,
    }
    return render(request, 'core/home.html', context)

def about(request):
    return render(request, 'core/about.html')

def package_list(request):
    packages = HealthPackage.objects.filter(is_active=True)
    return render(request, 'core/packages.html', {'packages': packages})

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            validate_phone_number(phone)
        except ValidationError as e:
            # Render with error instead of redirect to show inline
            return render(request, 'core/contact.html', {'phone_error': e.message})

        ContactMessage.objects.create(
            name=name, email=email, phone=phone,
            subject=subject, message=message
        )
        messages.success(request, "Thank you! Your message has been sent.")
        return redirect('contact')
    return render(request, 'core/contact.html')

def careers(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        position = request.POST.get('position')
        resume = request.FILES.get('resume')
        
        if resume:
            try:
                validate_phone_number(phone)
                CareerApplication.objects.create(
                    name=name, email=email, phone=phone,
                    position=position, resume=resume
                )
                messages.success(request, "Application submitted successfully!")
            except ValidationError as e:
                # Render with error
                return render(request, 'core/careers.html', {'phone_error': e.message})
        else:
            messages.error(request, "Please upload your resume.")
        return redirect('careers')
    return render(request, 'core/careers.html')

def international(request):
    return render(request, 'core/international.html')

def insurance_tpa(request):
    return render(request, 'core/insurance.html')

def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def admin_access(request):
    """
    Check if user has admin privileges.
    If yes, redirect to actual Django Admin.
    If no, show error message and redirect back.
    """
    if request.user.is_superuser:
        return redirect('/admin/')
    else:
        messages.error(request, "You dont have Admin previleges to change the Critical information")
        return redirect('staff_dashboard')
