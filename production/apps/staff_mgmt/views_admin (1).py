from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.decorators import group_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import StaffProfile, Shift, Attendance
from apps.core.utils_logging import log_admin_action
from doctors.models import Doctor, Department
from core.models import HealthPackage, GalleryImage
from .forms import (
    StaffUserCreationForm, StaffProfileForm, StaffUserChangeForm,
    DoctorProfileForm, DepartmentForm, 
    ShiftForm, HealthPackageForm, GalleryImageForm
)

@login_required
@group_required('Hospital Admins')
def admin_dashboard(request):
    # Auto Check-in Logic
    if hasattr(request.user, 'staff_profile'):
        profile = request.user.staff_profile
        today = timezone.now().date()
        if not Attendance.objects.filter(staff=profile, date=today).exists():
            Attendance.objects.create(
                staff=profile,
                date=today,
                check_in=timezone.now().time(),
                status='present'
            )
            log_admin_action(request.user, "Auto Check-in", f"Marked present for {today}")

    context = {
        'total_doctors': Doctor.objects.count(),
        'total_staff': StaffProfile.objects.count(),
        'active_packages': HealthPackage.objects.filter(is_active=True).count(),
        'departments_count': Department.objects.count(),
        'recent_staff': StaffProfile.objects.select_related('user').order_by('-joining_date')[:5]
    }
    return render(request, 'staff_mgmt/admin/dashboard.html', context)

# --- Staff Management ---
@login_required
@group_required('Hospital Admins')
def staff_list(request):
    staff_members = StaffProfile.objects.select_related('user', 'shift').all()
    return render(request, 'staff_mgmt/admin/staff_list.html', {'staff_members': staff_members})

@login_required
@group_required('Hospital Admins')
def staff_create(request):
    if request.method == 'POST':
        user_form = StaffUserCreationForm(request.POST)
        profile_form = StaffProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            # Assign to 'Staff' group if needed, logic omitted for simplicity
            
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            log_admin_action(request.user, "Create Staff", f"Created staff {user.username}")
            messages.success(request, f"Staff {user.get_full_name()} created successfully.")
            return redirect('staff_list')
    else:
        user_form = StaffUserCreationForm()
        profile_form = StaffProfileForm()
    
    return render(request, 'staff_mgmt/admin/staff_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Add New Staff'
    })

@login_required
@group_required('Hospital Admins')
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    user = profile.user
    
    if request.method == 'POST':
        user_form = StaffUserChangeForm(request.POST, instance=user)
        profile_form = StaffProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            log_admin_action(request.user, "Edit Staff", f"Updated details for {user.username}")
            messages.success(request, f"Staff {user.get_full_name()} updated successfully.")
            return redirect('staff_list')
    else:
        user_form = StaffUserChangeForm(instance=user)
        profile_form = StaffProfileForm(instance=profile)
    
    return render(request, 'staff_mgmt/admin/staff_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Edit Staff Member'
    })

# --- Doctor Management ---
@login_required
@group_required('Hospital Admins')
def doctor_list(request):
    doctors = Doctor.objects.select_related('user', 'department').all()
    return render(request, 'staff_mgmt/admin/doctor_list.html', {'doctors': doctors})

@login_required
@group_required('Hospital Admins')
def doctor_create(request):
    if request.method == 'POST':
        user_form = StaffUserCreationForm(request.POST) # Reuse generic user creation
        profile_form = DoctorProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.name = f"{user.first_name} {user.last_name}" # Sync name
            profile.save()
            messages.success(request, f"Doctor {profile.name} added successfully.")
            return redirect('doctor_list')
    else:
        user_form = StaffUserCreationForm()
        profile_form = DoctorProfileForm()
        
    return render(request, 'staff_mgmt/admin/doctor_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Add New Doctor'
    })

# --- Department Management ---
@login_required
@group_required('Hospital Admins')
def department_list(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created.")
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'staff_mgmt/admin/departments.html', {'departments': departments, 'form': form})

# --- Shift Management ---
@login_required
@group_required('Hospital Admins')
def shift_list(request):
    shifts = Shift.objects.all()
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Shift created.")
            return redirect('shift_list')
    else:
        form = ShiftForm()
    return render(request, 'staff_mgmt/admin/shifts.html', {'shifts': shifts, 'form': form})

# --- Gallery Management ---
@login_required
@group_required('Hospital Admins')
def gallery_list(request):
    images = GalleryImage.objects.all()
    return render(request, 'staff_mgmt/admin/gallery_list.html', {'images': images})

@login_required
@group_required('Hospital Admins')
def gallery_upload(request):
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            log_admin_action(request.user, "Gallery Upload", "Uploaded new image")
            messages.success(request, "Image uploaded successfully.")
            return redirect('gallery_list')
    else:
        form = GalleryImageForm()
    
    return render(request, 'staff_mgmt/admin/gallery_form.html', {'form': form, 'title': 'Upload Image'})

@login_required
@group_required('Hospital Admins')
def gallery_delete(request, pk):
    image = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        image.delete()
        log_admin_action(request.user, "Gallery Delete", f"Deleted image {pk}")
        messages.success(request, "Image deleted.")
    return redirect('gallery_list')

# --- Attendance Management ---
@login_required
@group_required('Hospital Admins')
def attendance_list(request):
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
        
    attendance_records = Attendance.objects.filter(date=selected_date).select_related('staff__user').order_by('-check_in')
    
    return render(request, 'staff_mgmt/admin/attendance_list.html', {
        'attendance_records': attendance_records,
        'selected_date': selected_date
    })
