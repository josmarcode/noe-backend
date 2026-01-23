from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Vehicle(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    brand       = models.CharField(max_length=50)
    model       = models.CharField(max_length=50)
    year        = models.PositiveIntegerField()
    name        = models.CharField(max_length=100)
    kilometers  = models.PositiveIntegerField()
    
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    active      = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    
