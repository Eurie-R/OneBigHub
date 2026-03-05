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
