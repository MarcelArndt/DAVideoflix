from django.db import models
from django.contrib.auth.models import AbstractUser

class Profiles(AbstractUser):
  
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email_is_confirmed = models.BooleanField(default=False)
    email_token = models.CharField(max_length=255, blank=True, null=True)
    profil_picture= models.ImageField(blank=True)
    
    USERNAME_FIELD = 'username'
    
    def __str__(self):
        return self.email or self.username