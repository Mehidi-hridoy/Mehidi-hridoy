from django.db import models

class Lead(models.Model):
    sl = models.AutoField(primary_key=True)
    create_date = models.DateTimeField(auto_now_add=True)
    customer_name = models.CharField(max_length=100)  # Mandatory
    mobile = models.CharField(max_length=11, blank=False, null=False)  # Mandatory
    all_project = models.CharField(max_length=200, blank=True, null=True)
    followup = models.DateField(blank=True, null=True)
    lead_type = models.CharField(max_length=50, choices=[
        ('Hot', 'Hot'),
        ('Warm', 'Warm'),
        ('Cold', 'Cold'),
        ('Normal', 'Normal'),
    ]) # Mandatory
    associate = models.CharField(max_length=100, blank=True, null=True)
    team_leader = models.CharField(max_length=100, choices=[
        ('Razib', 'Razib'),
        ('Rahim', 'Rahim')],blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    last_discussion = models.TextField(blank=True, null=True)
    next_followup = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.lead_id:  # Only generate if lead_id is empty or None
            last_lead = Lead.objects.order_by('-sl').first()
            if last_lead and last_lead.lead_id:
                try:
                    last_id = int(last_lead.lead_id.split('-')[1])
                    new_id = f"P-{str(last_id + 1).zfill(3)}"
                except (ValueError, IndexError):
                    new_id = "P-001"  # Fallback if parsing fails
            else:
                new_id = "P-001"
            self.lead_id = new_id
        super().save(*args, **kwargs)

    lead_id = models.CharField(max_length=50, unique=True, editable=False)

    def __str__(self):
        return f"{self.customer_name} - {self.lead_id}"
    


git remote add origin https://github.com/Mehidi-hridoy/Mehidi-hridoy.git
