from django.db import models

# Create your models here.
# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


# ─────────────────────────────────────────────
# Custom User Model
# Extends Django's AbstractUser to add role-based access
# REQ: SRS 4.1.2 - Role Identification
# ─────────────────────────────────────────────

class User(AbstractUser):

    class Role(models.TextChoices):
        ORGANIZATION = 'ORGANIZATION', 'Student Organization'
        ADMIN_OFFICE = 'ADMIN_OFFICE', 'Administrative Office'

    # Override email to make it the unique identifier
    email = models.EmailField(unique=True)

    # Role assigned on first login (SRS 4.1.2)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        null=True,
        blank=True
    )

    # Use email instead of username to log in
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def is_org(self):
        return self.role == self.Role.ORGANIZATION

    @property
    def is_admin_office(self):
        return self.role == self.Role.ADMIN_OFFICE


# ─────────────────────────────────────────────
# Officer Model
# Linked to an Organization Profile
# REQ: SRS 4.1.2 Sub-Feature 4 - List of officers (names and roles)
# ─────────────────────────────────────────────

class Officer(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)  # e.g. President, Secretary

    def __str__(self):
        return f"{self.name} - {self.position}"


# ─────────────────────────────────────────────
# Organization Profile
# Created automatically on first login for org users
# REQ: SRS 4.1.2 Sub-Feature 4
# ─────────────────────────────────────────────

class OrganizationProfile(models.Model):
    # Link to the user account
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='org_profile'
    )

    # Required fields (SRS 4.1.2 Sub-Feature 4)
    org_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    moderator_name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20)

    # Officers list (SRS 4.1.2 Sub-Feature 4)
    officers = models.ManyToManyField(
        Officer,
        blank=True,
        related_name='organizations'
    )

    # Optional fields (SRS 4.1.2 Sub-Feature 4)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(
        upload_to='org_logos/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.org_name


# ─────────────────────────────────────────────
# Administrative Office Profile
# Created automatically on first login for admin office users
# REQ: SRS 4.1.2 Sub-Feature 5
# ─────────────────────────────────────────────

class AdminOfficeProfile(models.Model):

    class OfficeType(models.TextChoices):
        CFMO = 'CFMO', 'Central Facilities Management Office'
        OSA  = 'OSA',  'Office of Student Activities'
        CSMO = 'CSMO', 'Campus Security Management Office'
        OTHER = 'OTHER', 'Other'

    # Link to the user account
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )

    # Required fields (SRS 4.1.2 Sub-Feature 5)
    office_name = models.CharField(max_length=200)
    office_type = models.CharField(
        max_length=10,
        choices=OfficeType.choices,
        default=OfficeType.OTHER
    )
    contact_email = models.EmailField()
    building = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.office_name