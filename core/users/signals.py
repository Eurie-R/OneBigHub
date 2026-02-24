from django.db.models.signals import post_save
from allauth.socialaccount.signals import social_account_added, pre_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.dispatch import receiver
from .models import OrganizationProfile, AdminOfficeProfile

User = get_user_model()

# ─────────────────────────────────────────────
# Allowed Ateneo email domains
# REQ: SRS 2.5 - Restricted to Ateneo Google Workspace accounts
# ─────────────────────────────────────────────

ALLOWED_DOMAINS = ['student.ateneo.edu', 'ateneo.edu']


# ─────────────────────────────────────────────
# Signal 1: Block non-Ateneo emails BEFORE login
# Fires before a social login is finalized
# REQ: SRS 2.5 - Authentication restricted to Ateneo domains
# ─────────────────────────────────────────────

@receiver(pre_social_login)
def restrict_to_ateneo_domain(sender, request, sociallogin, **kwargs):
    email = sociallogin.account.extra_data.get('email', '')
    domain = email.split('@')[-1] if '@' in email else ''

    if domain not in ALLOWED_DOMAINS:
        raise ImmediateHttpResponse(
            HttpResponseForbidden(
                "Access denied. Only Ateneo Google Workspace accounts "
                "(@student.ateneo.edu or @ateneo.edu) are allowed."
            )
        )


# ─────────────────────────────────────────────
# Signal 2: Auto-assign role based on email domain
# @student.ateneo.edu → ORGANIZATION
# @ateneo.edu         → ADMIN_OFFICE
# REQ: SRS 4.1.2 Sub-Feature 2 - Role Identification
# ─────────────────────────────────────────────

@receiver(social_account_added)
def assign_role_on_first_login(sender, request, sociallogin, **kwargs):
    user = sociallogin.user
    email = user.email
    domain = email.split('@')[-1] if '@' in email else ''

    if domain == 'student.ateneo.edu':
        user.role = User.Role.ORGANIZATION
    elif domain == 'ateneo.edu':
        user.role = User.Role.ADMIN_OFFICE

    user.save()


# ─────────────────────────────────────────────
# Signal 3: Auto-create profile on first login
# Fires after User is saved
# REQ: SRS 4.1.2 Sub-Feature 3, 4, 5 - Profile Creation
# ─────────────────────────────────────────────

@receiver(post_save, sender=User)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    if not created:
        return  # only run on first creation

    if instance.role == User.Role.ORGANIZATION:
        # Only create if profile doesn't exist yet
        OrganizationProfile.objects.get_or_create(
            user=instance,
            defaults={
                'org_name': '',        # to be filled in by user later
                'contact_email': instance.email,
                'moderator_name': '',
                'building': '',
                'room_number': '',
            }
        )

    elif instance.role == User.Role.ADMIN_OFFICE:
        AdminOfficeProfile.objects.get_or_create(
            user=instance,
            defaults={
                'office_name': '',     # to be filled in by user later
                'contact_email': instance.email,
                'building': '',
                'room_number': '',
            }
        )