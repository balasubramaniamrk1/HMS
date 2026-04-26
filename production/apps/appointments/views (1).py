from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import datetime
from .forms import AppointmentRequestForm
from .models import AppointmentRequest, Consultation

def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentRequestForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            
            # --- Patient ID Integration ---
            from core.models import Patient
            phone = form.cleaned_data.get('phone')
            
            # Look up existing patient (DO NOT CREATE NEW ONE)
            patient = Patient.objects.filter(phone=phone).first()
            
            if patient:
                appointment.patient = patient
                msg = f'Your appointment request has been received. Your Patient ID is {patient.patient_id}'
            else:
                # New patient: Defer creation
                appointment.patient = None
                msg = 'Your appointment request has been received. A Patient ID will be assigned after consultation.'
                
            appointment.save()

            messages.success(request, msg)
            return redirect('book_appointment')
    else:
        # Check for prefill data from GET request (e.g. from Staff Dashboard)
        initial_data = {}
        if request.GET.get('name'):
            initial_data['name'] = request.GET.get('name')
        if request.GET.get('phone'):
            initial_data['phone'] = request.GET.get('phone')
        if request.GET.get('doctor'):
            initial_data['doctor'] = request.GET.get('doctor')
            
        form = AppointmentRequestForm(initial=initial_data)
    return render(request, 'appointments/appointment_form.html', {'form': form})

# --- Staff Views ---

@login_required
def staff_dashboard(request):
    # --- Role Based Data Fetching ---
    user_groups = request.user.groups.values_list('name', flat=True)
    
    # Flags
    is_inventory_manager = 'Inventory Managers' in user_groups
    is_doctor = 'Doctors' in user_groups
    is_receptionist = 'Receptionists' in user_groups or 'Receptionist' in user_groups
    is_nurse = 'Nurses' in user_groups or 'Nurse' in user_groups
    
    # 1. Appointments (Doctors, Receptionists, Nurses)
    show_appointments = is_doctor or is_receptionist or is_nurse
    appointments = []
    if show_appointments:
        appointments = AppointmentRequest.objects.all().order_by('-created_at')

    # 2. Inventory Stats (Inventory Managers)
    inventory_stats = {}
    if is_inventory_manager:
        from inventory.models import Consumable, MaintenanceContract
        
        low_stock_count = len([c for c in Consumable.objects.all() if c.is_low_stock()])
        
        today = timezone.now().date()
        next_30 = today + timedelta(days=30)
        expiring_amcs = MaintenanceContract.objects.filter(contract_end__range=[today, next_30]).count()
        
        inventory_stats = {
            'low_stock_count': low_stock_count,
            'expiring_amcs': expiring_amcs,
        }

    # --- Dynamic Dashboard Titles ---
    dashboard_title = "Staff Administration"
    dashboard_subtitle = "Manage Appointments and Schedules"
    
    if is_inventory_manager:
        dashboard_title = "Inventory Manager Dashboard"
        dashboard_subtitle = "Manage Assets, Contracts, and Supplies"
    elif is_doctor:
        dashboard_title = "Doctor Console"
        dashboard_subtitle = "Manage Patient Appointments and Consultations"
    elif is_receptionist or is_nurse:
        dashboard_title = "Front Desk Dashboard"
        dashboard_subtitle = "Manage Appointments and Patient Flow"

    # --- Integration: Attendance Widget ---
    todays_attendance = None
    work_duration = "-- : --"
    staff_initials = ""
    staff_name = ""
    staff_designation = ""

    try:
        if hasattr(request.user, 'staff_profile'):
            from staff_mgmt.models import Attendance
            # Local imports removed to avoid UnboundLocalError
            
            profile = request.user.staff_profile
            staff_name = profile.user.get_full_name()
            staff_designation = profile.designation
            
            # Calculate initials safely
            fname = profile.user.first_name if profile.user.first_name else ""
            lname = profile.user.last_name if profile.user.last_name else ""
            staff_initials = (fname[:1] + lname[:1]).upper()

            today = timezone.now().date()
            # Get all sessions for today
            all_sessions = Attendance.objects.filter(staff=profile, date=today)
            
            # Identify current active session
            todays_attendance = all_sessions.filter(check_out__isnull=True).last()
            
            # --- Auto Check-In Logic ---
            # If no active session, but we have prior sessions today, AND user just logged in (e.g. < 2 mins ago)
            # then auto-start a new session.
            if not todays_attendance and all_sessions.exists():
                login_delta = timezone.now() - request.user.last_login
                # Using 120 seconds as a safe "just logged in" window
                if login_delta.total_seconds() < 120:
                    Attendance.objects.create(
                        staff=profile,
                        date=today,
                        check_in=timezone.now().time(),
                        status='present'
                    )
                    # Refresh query to get the new session
                    all_sessions = Attendance.objects.filter(staff=profile, date=today)
                    todays_attendance = all_sessions.filter(check_out__isnull=True).last()
            
            # If still no open session, use the last closed one for display
            if not todays_attendance:
                todays_attendance = all_sessions.last()
            
            total_seconds = 0
            
            for session in all_sessions:
                if session.check_in:
                    start_dt = datetime.datetime.combine(today, session.check_in)
                    if session.check_out:
                        end_dt = datetime.datetime.combine(today, session.check_out)
                    else:
                        # Ongoing session
                        end_dt = datetime.datetime.combine(today, timezone.now().time())
                    
                    if end_dt >= start_dt:
                        total_seconds += int((end_dt - start_dt).total_seconds())

            if total_seconds > 0:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                work_duration = f"{hours}h {minutes}m"

    except Exception as e:
        print(f"Error calculating attendance: {e}")
        todays_attendance = None
    
    return render(request, 'appointments/staff_dashboard.html', {
        'appointments': appointments,
        'show_appointments': show_appointments,
        
        'is_inventory_manager': is_inventory_manager,
        'inventory_stats': inventory_stats,

        'todays_attendance': todays_attendance,
        'work_duration': work_duration,
        'staff_initials': staff_initials,
        'staff_name': staff_name,
        'staff_designation': staff_designation,
        
        'dashboard_title': dashboard_title,
        'dashboard_subtitle': dashboard_subtitle
    })

@login_required
def update_status(request, pk, status):
    appointment = get_object_or_404(AppointmentRequest, pk=pk)
    if status in ['confirmed', 'cancelled', 'completed']:
        appointment.status = status
        appointment.save()
        messages.success(request, f"Appointment status updated to {status}.")
    return redirect('staff_dashboard')

from core.decorators import group_required

# --- Doctor Views ---
@login_required
def doctor_console(request):
    # Allow Doctors OR Superusers/Admins
    is_doctor = request.user.groups.filter(name='Doctors').exists()
    is_admin = request.user.is_superuser
    
    if not (is_doctor or is_admin):
        messages.error(request, "Access Denied: You do not have permission to view the Doctor Console.")
        return redirect('home')
        
    # Filter by logged-in doctor if applicable
    appointments = AppointmentRequest.objects.filter(status='confirmed')
    
    if hasattr(request.user, 'doctor_profile'):
        appointments = appointments.filter(doctor=request.user.doctor_profile)
        
    appointments = appointments.order_by('preferred_date')
    today = timezone.now().date()
    return render(request, 'appointments/doctor_console.html', {'appointments': appointments, 'today': today})

@login_required
def consultation_view(request, pk):
    appointment = get_object_or_404(AppointmentRequest, pk=pk)
    
    # Permission Check
    is_doctor = request.user.groups.filter(name='Doctors').exists()
    is_admin = request.user.is_superuser
    
    if not (is_doctor or is_admin):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if request.method == 'POST':
        # STRICT WRITE PROTECTION: Only Doctors can save
        if not is_doctor:
            messages.error(request, "Permission Denied: Only Doctors can prescribe medicines and complete consultations.")
            return redirect('doctor_console')

        diagnosis = request.POST.get('diagnosis', '').strip()
        diagnosis = request.POST.get('diagnosis', '').strip()
        notes = request.POST.get('notes', '').strip()
        doctor_comments = request.POST.get('doctor_comments', '').strip()
        
        # Lists from dynamic form
        medicine_names = request.POST.getlist('medicine_name[]')
        dosages = request.POST.getlist('dosage[]')
        durations = request.POST.getlist('duration[]')
        instructions = request.POST.getlist('instruction[]')
        
        # Server-side validation
        if not diagnosis or not notes:
            messages.error(request, "Diagnosis and Notes are mandatory.")
            return render(request, 'appointments/consultation_form.html', {'appointment': appointment})

        # --- Defer Patient Creation Logic ---
        if not appointment.patient:
            from core.models import Patient
            # Create the patient record now
            patient, created = Patient.objects.get_or_create(
                phone=appointment.phone,
                defaults={
                    'name': appointment.name,
                    'email': appointment.email
                }
            )
            appointment.patient = patient
            appointment.save()
            messages.info(request, f"New Patient Record Created. ID: {patient.patient_id}")

        # Create Consultation
        consultation = Consultation.objects.create(
            appointment=appointment,
            diagnosis=diagnosis,
            doctor_notes=notes,
            doctor_comments=doctor_comments,
            # We will populate the string field as a summary
            prescription="\n".join([f"{m} - {d} - {dur}" for m, d, dur in zip(medicine_names, dosages, durations)])
        )
        
        # Create Prescription Items
        from .models import PrescriptionItem
        
        for i in range(len(medicine_names)):
            if medicine_names[i]: # Avoid empty rows
                PrescriptionItem.objects.create(
                    consultation=consultation,
                    medicine_name=medicine_names[i],
                    dosage=dosages[i] if i < len(dosages) else '',
                    duration=durations[i] if i < len(durations) else '',
                    instruction=instructions[i] if i < len(instructions) else ''
                )

        # Mark as completed
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, "Consultation recorded successfully with prescription.")
        return redirect('doctor_console')

    return render(request, 'appointments/consultation_form.html', {
        'appointment': appointment,
        'is_read_only': not is_doctor  # If not a doctor (e.g. Admin), it's read-only
    })

@login_required
def reports_dashboard(request):
    from doctors.models import Doctor

    # RBAC: Check if logged-in user is a doctor
    current_doctor = None
    if hasattr(request.user, 'doctor_profile'):
        current_doctor = request.user.doctor_profile

    # RBAC: Deny access if not Doctor AND not Superuser
    if not current_doctor and not request.user.is_superuser:
        from django.contrib import messages
        messages.error(request, "Access Denied: You do not have permission to view Reports.")
        return redirect('home')

    # Get filters from request
    doctor_id = request.GET.get('doctor')
    if current_doctor:
        # User is a doctor, FORCE their ID
        doctor_id = current_doctor.id
    
    patient_name = request.GET.get('patient_name')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Base QuerySet
    consultations = Consultation.objects.all().select_related('appointment', 'appointment__doctor').order_by('-consultation_date')

    today = timezone.now().date()
    trigger = request.GET.get('trigger')

    # Date Logic based on Trigger
    if trigger == 'doctor_change':
        # Auto-set to last 30 days
        date_from = (today - timezone.timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
        # We enforce these dates for filtering regardless of what was in the URL (if any)
    elif trigger == 'filter_btn':
        # Validate dates are present (skipped if patient name is searched)
        if (not date_from or not date_to) and not patient_name:
            from django.contrib import messages
            messages.error(request, "Please select both From Date and To Date to filter.")
            # Do NOT filter by date if missing
            date_from = None
            date_to = None
    else:
        pass

    # Apply Filters
    selected_doctor_id = None
    
    if doctor_id:
        consultations = consultations.filter(appointment__doctor_id=doctor_id)
        try:
            selected_doctor_id = int(doctor_id)
        except (ValueError, TypeError):
            selected_doctor_id = None
    
    if patient_name:
        consultations = consultations.filter(appointment__name__icontains=patient_name)
        
    if date_from:
        consultations = consultations.filter(consultation_date__date__gte=date_from)
        
    if date_to:
        consultations = consultations.filter(consultation_date__date__lte=date_to)

    # --- Global Dashboard Stats Calculation ---
    from django.db.models import Count
    
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Total Patients (Unique in filtered set)
    patients_count = consultations.values('appointment__name').distinct().count()
    
    # 2. Monthly Consultations (In filtered context, restricted to current month)
    monthly_consultations = consultations.filter(consultation_date__gte=month_start).count()
    
    # 3. Top Diagnosis
    top_diagnosis_data = consultations.values('diagnosis').annotate(count=Count('diagnosis')).order_by('-count').first()
    top_diagnosis = top_diagnosis_data['diagnosis'] if top_diagnosis_data else "N/A"
    if top_diagnosis and len(top_diagnosis) > 30:
            top_diagnosis = top_diagnosis[:27] + "..."

    dashboard_stats = {
        'total_patients': patients_count,
        'monthly_consultations': monthly_consultations,
        'top_diagnosis': top_diagnosis
    }

    # Context data
    doctors = Doctor.objects.all()
    
    # Simple stats for the filtered set
    total_consultations = consultations.count()
    
    context = {
        'consultations': consultations,
        'doctors': doctors,
        'total_consultations': total_consultations,
        'selected_doctor_id': selected_doctor_id,
        'dashboard_stats': dashboard_stats,
        'current_doctor': current_doctor, # For template logic
    }
    return render(request, 'appointments/reports.html', context)
@login_required
def consultation_detail_view(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    return render(request, 'appointments/consultation_detail.html', {'consultation': consultation})

@login_required
def reschedule_appointment(request, pk):
    appointment = get_object_or_404(AppointmentRequest, pk=pk)
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        if new_date:
            appointment.preferred_date = new_date
            # Check if it was completed/cancelled returning to confirmed? 
            # For now, just keep it confirmed if rescheduling from confirmed.
            appointment.status = 'confirmed' 
            appointment.save()
            messages.success(request, f"Appointment rescheduled to {new_date}.")
        else:
            messages.error(request, "Please provide a valid date.")
    return redirect('doctor_console')

@login_required
def cancel_appointment_doctor(request, pk):
    appointment = get_object_or_404(AppointmentRequest, pk=pk)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, "Appointment cancelled.")
    return redirect('doctor_console')

from django.http import HttpResponse
from .utils import generate_prescription_pdf

@login_required
def download_prescription_pdf(request, consultation_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id)
    pdf_buffer = generate_prescription_pdf(consultation)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="prescription_{consultation.appointment.id}.pdf"'
    return response
