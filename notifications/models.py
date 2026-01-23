from django.db import models
from django.conf import settings
from vehicles.models import Vehicle
from trackers.models import Tracker

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True
    )
    
    tracker = models.ForeignKey(
        Tracker,
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True
    )
    
    type = models.CharField(max_length=50)
    channel = models.CharField(max_length=50)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('read', 'Read')
        ],
        default='pending'
    )
    
    scheduled_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)