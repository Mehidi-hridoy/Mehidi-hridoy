from django.shortcuts import render, redirect
from .models import Lead
from .forms import LeadForm

# Form submission view
def add_lead(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LeadForm()
    return render(request, 'crm/add_lead.html', {'form': form})

# Dashboard view
def dashboard(request):
    leads = Lead.objects.all()
    total_leads = leads.count()
    hot_leads = leads.filter(lead_type='Hot').count()
    warm_leads = leads.filter(lead_type='Warm').count()
    cold_leads = leads.filter(lead_type='Cold').count()
    normal_leads = leads.filter(lead_type='Normal').count()
    context = {
        'leads': leads,
        'total_leads': total_leads,
        'hot_leads': hot_leads,
        'warm_leads': warm_leads,
        'cold_leads': cold_leads,
        'normal_leads': normal_leads,
    }
    return render(request, 'crm/dashboard.html', context)