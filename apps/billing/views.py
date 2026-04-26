from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Invoice

@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST' and 'mark_paid' in request.POST:
        invoice.status = 'paid'
        invoice.save()
        # Ideally we would create a Payment record here too, but for now just updating status is sufficient per user request.
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
        
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})

@login_required
def dashboard(request):
    invoices = Invoice.objects.all().order_by('-date')
    
    # --- Analytics Data ---
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    import json
    from django.utils import timezone
    from datetime import timedelta

    # 1. Monthly Revenue (Last 6 Months)
    six_months_ago = timezone.now().date() - timedelta(days=180)
    revenue_data = (
        Invoice.objects.filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )
    
    chart_revenue = {
        'labels': [d['month'].strftime('%b %Y') for d in revenue_data],
        'values': [float(d['total']) for d in revenue_data]
    }

    # 2. Payment Status Breakdown
    status_data = (
        Invoice.objects.values('status')
        .annotate(count=Count('id'))
    )
    chart_status = {
        'labels': [s['status'].capitalize() for s in status_data],
        'values': [s['count'] for s in status_data]
    }

    return render(request, 'billing/dashboard.html', {
        'invoices': invoices,
        'chart_revenue_json': json.dumps(chart_revenue),
        'chart_status_json': json.dumps(chart_status),
    })
