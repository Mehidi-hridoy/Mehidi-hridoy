from django import forms
from .models import Lead

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'customer_name', 'mobile', 'all_project', 'followup', 'lead_type',
            'associate', 'team_leader', 'notes', 'source', 'last_discussion',
            'next_followup'
        ]  # Exclude lead_id as it’s auto-generated
        widgets = {
            'followup': forms.DateInput(attrs={'type': 'date'}),
            'next_followup': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make customer_name and lead_type required
        self.fields['customer_name'].required = True
        self.fields['mobile'].required = True # Make mobile required
        self.fields['lead_type'].required = True
        # Make other fields optional
        for field in ['mobile', 'all_project', 'followup', 'associate', 'team_leader', 
                      'notes', 'source', 'last_discussion', 'next_followup']:
            self.fields[field].required = False
            self.fields['mobile'].widget.attrs.update({'required': 'required'})

