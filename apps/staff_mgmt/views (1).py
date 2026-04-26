from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import StaffProfile, Attendance

def is_staff_member(user):
    return hasattr(user, 'staff_profile')

@login_required
@login_required
def staff_dashboard(request):
    # Permission Check
    if not hasattr(request.user, 'staff_profile'):
        if request.user.groups.filter(name='Hospital Admins').exists() or request.user.is_superuser:
            return redirect('admin_dashboard')
        messages.error(request, "Access Denied: You are not a staff member.")
        return redirect('home')

    attendance = Attendance.objects.filter(staff=request.user.staff_profile).order_by('-date', '-check_in')
    today = timezone.now().date()
    
    # Active session: One where check_out is NULL
    active_session = Attendance.objects.filter(staff=request.user.staff_profile, date=today, check_out__isnull=True).first()
    
    # Latest session for display info (could be a closed one)
    latest_session = Attendance.objects.filter(staff=request.user.staff_profile, date=today).first()
    
    return render(request, 'staff_mgmt/dashboard.html', {
        'attendance': attendance,
        'active_session': active_session,
        'latest_session': latest_session
    })

@login_required
@user_passes_test(is_staff_member)
@login_required
@user_passes_test(is_staff_member)
def check_in(request):
    if request.method == 'POST':
        today = timezone.now().date()
        profile = request.user.staff_profile
        
        # Check if there is already an OPEN session
        if Attendance.objects.filter(staff=profile, date=today, check_out__isnull=True).exists():
            messages.warning(request, "You are already currently checked in.")
        else:
            current_time = timezone.now().time()
            status = 'present'
            is_late = False
            
            # Late Arrival Logic
            if profile.shift:
                # Create datetime objects for comparison (combining with today)
                from datetime import datetime, timedelta
                now = datetime.combine(today, current_time)
                shift_start = datetime.combine(today, profile.shift.start_time)
                
                # Grace period of 15 minutes
                grace_period = timedelta(minutes=15)
                
                if now > (shift_start + grace_period):
                    is_late = True
                    status = 'late' # Optional: set main status to late or keep present
            
            Attendance.objects.create(
                staff=profile,
                date=today,
                check_in=current_time,
                status=status,
                is_late=is_late
            )
            
            if is_late:
                 messages.warning(request, f"Checked in late. Shift started at {profile.shift.start_time.strftime('%H:%M')}.")
            else:
                 messages.success(request, "Checked in successfully.")
            
    return redirect('staff_dashboard')

@login_required
@user_passes_test(is_staff_member)
def check_out(request):
    if request.method == 'POST':
        today = timezone.now().date()
        profile = request.user.staff_profile
        
        # Find the open session
        attendance = Attendance.objects.filter(staff=profile, date=today, check_out__isnull=True).last()
        
        if attendance:
            attendance.check_out = timezone.now().time()
            attendance.save()
            messages.success(request, "Checked out successfully.")
        else:
             messages.error(request, "No active session found to check out from.")
            
    return redirect('staff_dashboard')

@login_required
def attendance_report(request):
    # Admin or HR check ideally
    
    # Filters
    month = request.GET.get('month') # Format YYYY-MM
    department = request.GET.get('department')
    staff_id = request.GET.get('staff_id')
    
    queryset = Attendance.objects.select_related('staff', 'staff__user').all().order_by('-date')
    
    # Date Filtering
    if month:
        year, m = map(int, month.split('-'))
        queryset = queryset.filter(date__year=year, date__month=m)
    else:
        # Default to current month
        today = timezone.now().date()
        queryset = queryset.filter(date__year=today.year, date__month=today.month)
        month = today.strftime('%Y-%m') # For template value
        
    if department:
        queryset = queryset.filter(staff__department=department)
        
    if staff_id:
        queryset = queryset.filter(staff__id=staff_id)
        
    # Departments list for dropdown
    departments = StaffProfile.objects.values_list('department', flat=True).distinct()
    
    # Calculate stats for the filtered set
    total_present = queryset.filter(status__in=['present', 'late']).count()
    total_late = queryset.filter(is_late=True).count()
    total_absent = queryset.filter(status='absent').count()
    
    context = {
        'attendance_list': queryset,
        'departments': departments,
        'selected_department': department,
        'current_month': month,
        'stats': {
            'present': total_present,
            'late': total_late,
            'absent': total_absent
        }
    }
    return render(request, 'staff_mgmt/attendance_report.html', context)
