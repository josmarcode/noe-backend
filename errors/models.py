from django.db import models
from django.conf import settings
from access.models import Accesses

User = settings.AUTH_USER_MODEL

class Error(models.Model):
    access = models.ForeignKey(
        Accesses,
        on_delete=models.CASCADE,
        related_name='errors'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='errors'
    )
    
    source      = models.CharField(max_length=100)
    error_type  = models.CharField(max_length=100)
    error_code  = models.CharField(max_length=50)    
    message     = models.TextField()

    stack_trace = models.TextField(blank=True, null=True)
    context     = models.JSONField(blank=True, null=True)
    severity    = models.CharField(max_length=50)
    
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Error {self.error_code} - {self.source}"
    

