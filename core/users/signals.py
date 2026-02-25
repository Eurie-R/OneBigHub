from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import OrganizationProfile, AdminOfficeProfile

User = get_user_model()


# ─────────────────────────────────────────────
# Auto-create profile on user creation
# REQ: SRS 4.1.2 Sub-Feature 3, 4, 5
# ─────────────────────────────────────────────

@receiver(post_save, sender=User)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == User.Role.ORGANIZATION:
        OrganizationProfile.objects.get_or_create(
            user=instance,
            defaults={
                'org_name': '',
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
                'office_name': '',
                'contact_email': instance.email,
                'building': '',
                'room_number': '',
            }
        )