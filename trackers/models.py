from django.db import models
from vehicles.models import Vehicle

class Tracker(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='trackers'
    )
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True, null=True)
    
    unit = models.CharField(max_length=20, default='km')
    interval_value = models.PositiveIntegerField(default=1000)
    
    last_service_km = models.PositiveIntegerField(default=0)
    last_service_at = models.DateTimeField(blank=True, null=True)
    
    next_due_km = models.PositiveIntegerField(default=0)
    next_due_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"