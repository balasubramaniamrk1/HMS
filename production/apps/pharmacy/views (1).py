from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Medicine, Batch, Sale, SaleItem
from appointments.models import Consultation
from admissions.models import Admission
from doctors.models import Doctor
import json
from .models import Medicine, Batch, Sale, SaleItem, MedicineReturn, MedicineReturnItem
from .forms import MedicineForm

@login_required
def pharmacy_dashboard(request):
    # Fetch pending prescriptions
    # Only show consultations that have items in prescription and are pending
    pending_prescriptions = Consultation.objects.filter(
        pharmacy_status__in=['pending', 'partially_dispensed'],
        prescription_items__isnull=False
    ).distinct().order_by('-consultation_date')
    
    # Active IPD Admissions
    active_admissions = Admission.objects.filter(status='admitted').select_related('ward', 'bed', 'doctor').order_by('-admission_date')

    context = {
        'consultations': pending_prescriptions,
        'admissions': active_admissions
    }
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def pos_view(request):
    # Check for optional IDs
    consultation_id = request.GET.get('consultation_id')
    admission_id = request.GET.get('admission_id')
    
    prefill_cart = []
    unavailable_items = []
    consultation_obj = None
    admission_obj = None
    doctor_obj = None
    patient_name = ''
    
    if consultation_id:
        consultation_obj = get_object_or_404(Consultation, id=consultation_id)
        patient_name = consultation_obj.appointment.name
        doctor_obj = consultation_obj.appointment.doctor
        
        # Logic to map prescription items to batches
        for item in consultation_obj.prescription_items.all():
            med_name = item.medicine_name
            # Improved matching: Try exact first, then contains
            medicine = Medicine.objects.filter(name__iexact=med_name).first()
            if not medicine:
                medicine = Medicine.objects.filter(name__icontains=med_name).first()
            
            if medicine:
                # Find available batches (FIFO)
                batches = Batch.objects.filter(medicine=medicine, quantity__gt=0, expiry_date__gte=timezone.now().date()).order_by('expiry_date')
                
                batch = batches.first()
                
                if batch:
                    # Parse dosage to estimate quantity? Defaults to 1 for now.
                    qty = 1 
                    prefill_cart.append({
                        'id': str(batch.id),
                        'name': medicine.name,
                        'batch': batch.batch_number,
                        'price': float(batch.sell_price),
                        'quantity': qty,
                        'max': batch.quantity
                    })
                else:
                    unavailable_items.append({'name': med_name, 'reason': 'Out of Stock'})
            else:
                unavailable_items.append({'name': med_name, 'reason': 'Unknown Medicine'})

    elif admission_id:
        admission_obj = get_object_or_404(Admission, id=admission_id)
        patient_name = admission_obj.patient_name
        doctor_obj = admission_obj.doctor
        # IPD Request: Usually implies manual selection unless we add Prescription model for IPD later.
        # So prefill_cart remains empty for manual additions.

    if request.method == 'POST':
        try:
            with transaction.atomic():
                cart_data_json = request.POST.get('cart_data', '[]')
                cart_data = json.loads(cart_data_json)
                
                if not cart_data:
                    messages.error(request, "Cart is empty")
                    return redirect('pharmacy:pos')

                total_amount = 0
                
                # Fetch Consultation or Admission
                cons_id_post = request.POST.get('consultation_id')
                adm_id_post = request.POST.get('admission_id')
                cons_obj_post = None
                adm_obj_post = None

                if cons_id_post:
                    cons_obj_post = Consultation.objects.get(id=cons_id_post)
                if adm_id_post:
                    adm_obj_post = Admission.objects.get(id=adm_id_post)

                # 1. Create Invoice
                from billing.models import Invoice, InvoiceItem
                
                patient_name_post = request.POST.get('patient_name', 'Walk-in')
                doctor_id = request.POST.get('doctor_id')
                doctor_post = Doctor.objects.get(id=doctor_id) if doctor_id else None

                invoice = Invoice.objects.create(
                    patient_name=patient_name_post,
                    doctor=doctor_post,
                    consultation=cons_obj_post,
                    admission=adm_obj_post,
                    source='pharmacy',
                    status='pending',
                    total_amount=0
                )

                # 2. Create Sale linked to Invoice
                sale = Sale.objects.create(
                    patient_name=patient_name_post,
                    doctor=doctor_post,
                    consultation=cons_obj_post,
                    admission=adm_obj_post,
                    invoice=invoice,
                    status='completed'
                )

                for item in cart_data:
                    batch_id = item.get('batch_id')
                    try:
                        quantity = int(item.get('quantity'))
                    except (ValueError, TypeError):
                         messages.error(request, f"Invalid quantity for item {item.get('name')}")
                         raise ValueError("Invalid Quantity")

                    batch = Batch.objects.select_for_update().get(id=batch_id)
                    
                    if batch.quantity < quantity:
                        raise ValueError(f"Insufficient stock for {batch.medicine.name}")
                    
                    price = batch.sell_price
                    line_total = price * quantity
                    total_amount += line_total
                    
                    # Create SaleItem
                    SaleItem.objects.create(
                        sale=sale,
                        batch=batch,
                        quantity=quantity,
                        price_at_sale=price
                    )
                    
                    # Create InvoiceItem
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=f"{batch.medicine.name} (Batch: {batch.batch_number})",
                        quantity=quantity,
                        unit_price=price,
                        line_total=line_total
                    )

                # Update Totals
                invoice.total_amount = total_amount
                invoice.save()
                
                # Update Consultation Status
                # Update Consultation Status
                if cons_obj_post:
                    # Check if all prescribed items are in the invoice
                    prescribed_items_count = cons_obj_post.prescription_items.count()
                    invoiced_items_count = invoice.items.count()
                    
                    if invoiced_items_count >= prescribed_items_count:
                         cons_obj_post.pharmacy_status = 'dispensed'
                    elif invoiced_items_count > 0:
                         cons_obj_post.pharmacy_status = 'partially_dispensed'
                    else:
                         cons_obj_post.pharmacy_status = 'pending' # Should not happen on sale
                    
                    cons_obj_post.save()

                messages.success(request, f"Sale completed! Invoice #{invoice.id} generated.")
                return redirect('billing:invoice_detail', invoice_id=invoice.id)

        except Exception as e:
            messages.error(request, f"Error processing sale: {str(e)}")
            return redirect('pharmacy:pos')

    # GET request - Show POS interface
    
    # AJAX Search Handler
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('term'):
        term = request.GET.get('term')
        results = []
        matches = Batch.objects.filter(
            quantity__gt=0, 
            expiry_date__gte=timezone.now().date(),
            medicine__name__istartswith=term
        ).select_related('medicine').order_by('expiry_date')[:20] # Limit results
        
        for batch in matches:
            results.append({
                'id': batch.id,
                'name': batch.medicine.name,
                'generic': batch.medicine.generic_name,
                'batch': batch.batch_number,
                'expiry': batch.expiry_date.strftime('%b %d, %Y'),
                'price': float(batch.sell_price),
                'stock': batch.quantity
            })
        return JsonResponse(results, safe=False)

    # Standard Page Load
    # We do NOT load all batches by default anymore.
    
    context = {
        'prefill_cart': json.dumps(prefill_cart),
        'patient_name': patient_name,
        'doctor': doctor_obj,
        'consultation': consultation_obj,
        'admission': admission_obj,
        'unavailable_items': unavailable_items,
    }
    return render(request, 'pharmacy/pos.html', context)

@login_required
def stock_list(request):
    # Fetch all batches with medicine info
    batches = Batch.objects.select_related('medicine', 'medicine__category').order_by('medicine__name', 'expiry_date')
    
    # Check for low stock (simple check based on medicine reorder level vs total stock)
    # This is slightly complex in SQL with Batch split, so we do it in python for MVP or aggregation
    from django.db.models import Sum
    
    # Low Stock Alert Logic
    low_stock_medicines = []
    medicines = Medicine.objects.annotate(total_quantity=Sum('batches__quantity'))
    for med in medicines:
        if med.total_quantity is not None and med.total_quantity <= med.reorder_level:
            low_stock_medicines.append(med)
            
    # Check if user is a doctor for UI toggle
    is_doctor = request.user.groups.filter(name='Doctors').exists()

    context = {
        'batches': batches,
        'low_stock_medicines': low_stock_medicines,
        'is_doctor': is_doctor
    }
    return render(request, 'pharmacy/stock_list.html', context)

from .models import PurchaseOrder, PurchaseOrderItem, StockEntry
from inventory.models import Vendor

@login_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all().order_by('-date')
    return render(request, 'pharmacy/purchase_order_list.html', {'orders': orders})

@login_required
def purchase_order_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, 'pharmacy/purchase_order_detail.html', {'po': po})

@login_required
def purchase_order_create(request):
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        expected_date = request.POST.get('expected_date')
        
        # Simple logic: assume at least one item row
        # Items are passed as list arrays? or we can use a simple formset approach on frontend.
        # Let's keep it simple: 
        # cart_data sent as JSON similar to POS? Or dynamic form fields?
        # Let's use the JSON approach as we did in POS, it's cleaner for dynamic rows.
        
        try:
            with transaction.atomic():
                vendor = get_object_or_404(Vendor, id=vendor_id)
                po = PurchaseOrder.objects.create(
                    vendor=vendor,
                    expected_delivery_date=expected_date if expected_date else None,
                    created_by=request.user,
                    status='ordered' # Direct to ordered for now? Or pending?
                )
                
                items_json = request.POST.get('items_json', '[]')
                items = json.loads(items_json)
                
                total_val = 0
                for item in items:
                    med_id = item.get('medicine_id')
                    qty = int(item.get('quantity'))
                    price = float(item.get('price')) # Estimated
                    
                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        medicine_id=med_id,
                        quantity_requested=qty,
                        unit_price_expected=price
                    )
                    total_val += (price * qty)
                
                po.total_amount = total_val
                po.save()
                
                messages.success(request, f"Purchase Order #{po.id} created successfully.")
                return redirect('pharmacy:purchase_order_list')
        except Exception as e:
            messages.error(request, f"Error creating PO: {str(e)}")
    
    vendors = Vendor.objects.all()
    medicines = Medicine.objects.all().order_by('name')
    return render(request, 'pharmacy/purchase_order_form.html', {'vendors': vendors, 'medicines': medicines})

@login_required
def stock_entry_create(request):
    # If ?po_id=X is passed, verify against that PO
    po_id = request.GET.get('po_id')
    po = None
    if po_id:
        po = get_object_or_404(PurchaseOrder, id=po_id)
        if po.status in ['received', 'cancelled']:
             messages.error(request, f"Purchase Order #{po.id} is already {po.status}. Cannot process GRN.")
             return redirect('pharmacy:purchase_order_list')
    
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        invoice_no = request.POST.get('invoice_no')
        invoice_date = request.POST.get('invoice_date')
        
        try:
            with transaction.atomic():
                vendor = get_object_or_404(Vendor, id=vendor_id)
                
                # Create Stock Entry (GRN)
                stock_entry = StockEntry.objects.create(
                    purchase_order=po, # Link if exists
                    vendor=vendor,
                    vendor_invoice_number=invoice_no,
                    vendor_invoice_date=invoice_date if invoice_date else None,
                    received_by=request.user
                )
                
                # Process Items (JSON)
                items_json = request.POST.get('items_json', '[]')
                items = json.loads(items_json)
                
                for item in items:
                    med_id = item.get('medicine_id')
                    try:
                        batch_no = item['batch_no']
                        expiry = item['expiry']
                        qty = int(item['quantity'])
                        # Optional: buy price/sell price override?
                        buy_price = float(item.get('buy_price', 0))
                        sell_price = float(item.get('sell_price', 0))
                    except KeyError as e:
                        raise ValueError(f"Missing field: {str(e)}")

                    # Create Batch
                    Batch.objects.create(
                        medicine_id=med_id,
                        batch_number=batch_no,
                        expiry_date=expiry,
                        quantity=qty,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        vendor=vendor,
                        stock_entry=stock_entry
                    )
                
                # If linked to PO, mark PO as Received?
                if po:
                    po.status = 'received'
                    po.save()
                
                messages.success(request, f"Stock Entry #{stock_entry.id} saved. Inventory updated.")
                return redirect('pharmacy:stock_list')
        
        except Exception as e:
            messages.error(request, f"Error saving Stock Entry: {str(e)}")
    
    vendors = Vendor.objects.all()
    medicines = Medicine.objects.all().order_by('name')
    # Use 'ordered' status for POs waiting to be received. 'pending' might be drafts.
    # If your workflow uses 'pending' as 'sent to vendor', include that too.
    # Looking at purchase_order_create, it sets status='ordered'.
    pending_pos = PurchaseOrder.objects.filter(status__in=['pending', 'ordered']).order_by('-date')
    
    return render(request, 'pharmacy/stock_entry_form.html', {
        'vendors': vendors, 
        'medicines': medicines,
        'po': po,
        'pending_pos': pending_pos
    })

# ==========================
# REPORTING VIEWS
# ==========================
from datetime import timedelta
from django.db import models

@login_required
def reports_dashboard(request):
    # Summary Metrics
    today = timezone.now().date()
    
    # 1. Today's Sales
    # 1. Today's Sales
    todays_sales = Sale.objects.filter(date__date=today).count()
    todays_revenue = 0
    # Aggregation for revenue
    from django.db.models import Sum
    revenue_agg = SaleItem.objects.filter(sale__date__date=today).aggregate(total=Sum(models.F('quantity') * models.F('price_at_sale')))
    todays_revenue = revenue_agg['total'] or 0

    # 1b. Month to Date Sales
    start_of_month = today.replace(day=1)
    mtd_sales = Sale.objects.filter(date__date__gte=start_of_month, date__date__lte=today).count()
    
    mtd_revenue_agg = SaleItem.objects.filter(
        sale__date__date__gte=start_of_month, 
        sale__date__date__lte=today
    ).aggregate(total=Sum(models.F('quantity') * models.F('price_at_sale')))
    mtd_revenue = mtd_revenue_agg['total'] or 0

    # 2. Low Stock Count
    low_stock_count = 0
    all_meds = Medicine.objects.annotate(total_stock=Sum('batches__quantity'))
    for m in all_meds:
        if m.total_stock and m.total_stock <= m.reorder_level:
            low_stock_count += 1
            
    # 3. Expiring Soon (Next 30 Days)
    thirty_days_later = today + timedelta(days=30)
    expiring_count = Batch.objects.filter(expiry_date__range=[today, thirty_days_later], quantity__gt=0).count()

    # 4. Quick Insights Data
    # Top Selling Medicine (All time or last 30 days? Let's do last 30 days for relevance)
    last_30_days = today - timedelta(days=30)
    top_selling = SaleItem.objects.filter(sale__date__date__gte=last_30_days).values('batch__medicine__name').annotate(
        total_qty=models.Sum('quantity')
    ).order_by('-total_qty').first()

    # Total Inventory Value
    stock_value_agg = Batch.objects.filter(quantity__gt=0).aggregate(
        total=models.Sum(models.F('quantity') * models.F('buy_price'))
    )
    total_stock_value = stock_value_agg['total'] or 0

    # Pending Orders
    pending_pos_count = PurchaseOrder.objects.filter(status__in=['pending', 'ordered']).count()

    context = {
        'todays_sales': todays_sales,
        'todays_revenue': todays_revenue,
        'mtd_sales': mtd_sales,
        'mtd_revenue': mtd_revenue,
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count,
        
        # New Insights
        'top_selling': top_selling,
        'total_stock_value': total_stock_value,
        'pending_pos_count': pending_pos_count
    }
    return render(request, 'pharmacy/reports_dashboard.html', context)

@login_required
def sales_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    sales = Sale.objects.select_related('invoice', 'doctor').all().order_by('-date')
    
    if start_date and end_date:
        sales = sales.filter(date__date__range=[start_date, end_date])
    
    # Calculate Total Revenue for the filtered set
    total_revenue = 0
    for sale in sales:
        if sale.invoice:
            total_revenue += sale.invoice.total_amount
            
    return render(request, 'pharmacy/report_sales.html', {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue
    })

@login_required
def expiry_report(request):
    days = int(request.GET.get('days', 90)) # Default 90 days
    today = timezone.now().date()
    target_date = today + timedelta(days=days)
    
    expiring_batches = Batch.objects.filter(
        expiry_date__lte=target_date, 
        quantity__gt=0
    ).select_related('medicine').order_by('expiry_date')
    
    # Also fetch expired items that were returned (not restocked)
    from .models import MedicineReturnItem
    expired_returns = MedicineReturnItem.objects.filter(
        is_restocked=False
    ).select_related('medicine_return', 'sale_item__batch__medicine').order_by('-medicine_return__return_date')

    return render(request, 'pharmacy/report_expiry.html', {
        'batches': expiring_batches,
        'days': days,
        'expired_returns': expired_returns
    })

@login_required
def stock_report(request):
    # Detailed stock view with value
    batches = Batch.objects.filter(quantity__gt=0).select_related('medicine').order_by('medicine__name')
    
    total_stock_value = 0
    # Evaluate query to annotate in python
    batches_list = []
    for b in batches:
        b.line_total = b.quantity * b.buy_price
        total_stock_value += b.line_total
        batches_list.append(b)
        
    return render(request, 'pharmacy/report_stock.html', {
        'batches': batches_list,
        'total_stock_value': total_stock_value
    })

@login_required
def return_medicine(request):
    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        reason = request.POST.get('reason')
        items_json = request.POST.get('return_items', '[]')
        
        try:
            with transaction.atomic():
                sale = get_object_or_404(Sale, id=sale_id)
                items_data = json.loads(items_json)
                
                if not items_data:
                    messages.error(request, "No items selected for return.")
                    return redirect('pharmacy:report_sales')

                # Create Return Record
                med_return = MedicineReturn.objects.create(
                    sale=sale,
                    reason=reason,
                    processed_by=request.user,
                    total_refund_amount=0
                )
                
                total_refund = 0
                
                for item in items_data:
                    sale_item_id = item['sale_item_id']
                    qty_to_return = int(item['quantity'])
                    is_restock = item.get('is_restock', True)
                    
                    sale_item = SaleItem.objects.select_for_update().get(id=sale_item_id)
                    
                    if qty_to_return > sale_item.quantity:
                         raise ValueError(f"Cannot return more than sold quantity for {sale_item.batch.medicine.name}")
                    
                    # Calculate refund (Simple logic: linear proportion of sold price)
                    refund_val = sale_item.price_at_sale * qty_to_return
                    total_refund += refund_val
                    
                    MedicineReturnItem.objects.create(
                        medicine_return=med_return,
                        sale_item=sale_item,
                        quantity_returned=qty_to_return,
                        refund_amount=refund_val,
                        is_restocked=is_restock
                    )
                
                med_return.total_refund_amount = total_refund
                med_return.save()
                
                # Optional: Update Invoice to show refund or create Credit Note?
                # For now, just logging the return in Pharmacy system.
                
                messages.success(request, f"Return processed successfully. Refund Due: {total_refund}")
                return redirect('pharmacy:report_sales')
                
        except Exception as e:
            messages.error(request, f"Error processing return: {str(e)}")
            return redirect('pharmacy:report_sales')
            
    # GET: If sale_id provided, show return form
    sale_id = request.GET.get('sale_id')
    if sale_id:
        sale = get_object_or_404(Sale, id=sale_id)
        return render(request, 'pharmacy/return_form.html', {'sale': sale})
        
    return redirect('pharmacy:report_sales')

@login_required
def returns_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    reason_filter = request.GET.get('reason', '')
    
    returns = MedicineReturnItem.objects.select_related(
        'medicine_return', 'sale_item', 'sale_item__batch__medicine'
    ).order_by('-medicine_return__return_date')
    
    if start_date:
        returns = returns.filter(medicine_return__return_date__date__gte=start_date)
    if end_date:
        returns = returns.filter(medicine_return__return_date__date__lte=end_date)
    if reason_filter:
        if reason_filter == 'expired':
            returns = returns.filter(medicine_return__reason__icontains='expire')
        elif reason_filter == 'damaged':
            returns = returns.filter(medicine_return__reason__icontains='damage')
        else:
             returns = returns.filter(medicine_return__reason__icontains=reason_filter)

    total_refund = sum(item.refund_amount for item in returns)
    
    context = {
        'returns': returns,
        'start_date': start_date,
        'end_date': end_date,
        'reason_filter': reason_filter,
        'total_refund': total_refund
    }
    return render(request, 'pharmacy/report_returns.html', context)

@login_required
def medicine_create(request):
    # RBAC: Allow Hospital Admins, Pharmacy Managers (Inventory Managers)
    allowed_groups = ['Hospital Admins', 'Inventory Managers']
    is_allowed = request.user.groups.filter(name__in=allowed_groups).exists() or request.user.is_superuser
    
    if not is_allowed:
        messages.error(request, "Access Denied: You do not have permission to add new medicines.")
        return redirect('pharmacy:dashboard')

    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save()
            messages.success(request, f"Medicine '{medicine.name}' added successfully.")
            return redirect('pharmacy:stock_list')
    else:
        form = MedicineForm()
    
    return render(request, 'pharmacy/medicine_form.html', {'form': form})
