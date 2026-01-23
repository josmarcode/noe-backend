from django.db import models
from trackers.models import Tracker

class Register(models.Model):
    tracker = models.ForeignKey(
        Tracker,
        on_delete=models.CASCADE,
        related_name='registers'
    )
    
    kilometers = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tracker_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)