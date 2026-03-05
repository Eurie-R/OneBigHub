import os
from django.db import models
from django.core.exceptions import ValidationError
from users.models import OrganizationProfile


# ─────────────────────────────────────────────
# Validators
# REQ: SRS 4.3.4 - File type and size validation
# ─────────────────────────────────────────────
def validate_file_size_and_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Unsupported file extension. Allowed: PDF, DOCX, JPG, PNG.')
    
    # 5MB limit
    limit = 5242880
    if value.size > limit:
        raise ValidationError('File size cannot exceed 5MB.')


# ─────────────────────────────────────────────
# Proposal Class Model
# REQ: SRS 4.3.4 - REQ-1, REQ-5, REQ-13
# ─────────────────────────────────────────────
class Proposal(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    # REQ-13: Associate with organization profile
    organization = models.ForeignKey(
        OrganizationProfile, 
        on_delete=models.CASCADE, 
        related_name='proposals'
    )
    
    # Input interface fields (Blank=True allows for saving as draft without filling them)
    title = models.CharField(max_length=255, blank=True)
    nature_of_activity = models.CharField(max_length=200, blank=True)
    target_attendees = models.CharField(max_length=200, blank=True)
    objectives = models.TextField(blank=True)
    
    # Date and time scheduling
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    
    # Office selection
    reviewing_office = models.CharField(
        max_length=10, 
        choices=[('CFMO', 'CFMO'), ('OSA', 'OSA'), ('CSMO', 'CSMO'), ('OTHER', 'Other')],
        blank=True
    )

    # Status tracking
    status = models.CharField(
        max_length=15, 
        choices=Status.choices, 
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title if self.title else f"Untitled Draft - {self.organization.org_name}"