from django.core.exceptions import ValidationError

ALLOWED_DOMAINS = ['student.ateneo.edu', 'ateneo.edu']


def validate_ateneo_email(email):
    """
    Ensures only Ateneo email domains can register.
    REQ: SRS 2.5
    """
    domain = email.split('@')[-1] if '@' in email else ''

    if domain not in ALLOWED_DOMAINS:
        raise ValidationError(
            f"Only Ateneo email addresses are allowed. "
            f"(@student.ateneo.edu or @ateneo.edu)"
        )


def get_role_from_email(email):
    """
    Determines role based on email domain.
    REQ: SRS 4.1.2 Sub-Feature 2
    """
    domain = email.split('@')[-1] if '@' in email else ''

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if domain == 'student.ateneo.edu':
        return User.Role.ORGANIZATION
    elif domain == 'ateneo.edu':
        return User.Role.ADMIN_OFFICE
    return None