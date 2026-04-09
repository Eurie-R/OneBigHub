from django.db import models
from users.models import OrganizationProfile

# Create your models here.

class Post(models.Model):
    organization = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.CASCADE,
        related_name='posts'
    )

    title = models.CharField(max_length=255)
    body = models.TextField()

    event_start = models.DateTimeField(null=True, blank=True)
    event_end = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
