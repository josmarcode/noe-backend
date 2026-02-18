from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Accesses(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accesses'
    )
    
    method      = models.CharField(max_length=50)
    path        = models.CharField(max_length=200)
    status_code = models.PositiveIntegerField()
    ip_address  = models.GenericIPAddressField()
    
    duration_ms = models.PositiveIntegerField()
    created_at  = models.DateTimeField(auto_now_add=True)