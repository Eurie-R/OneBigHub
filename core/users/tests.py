from django.test import TestCase
from django.contrib.auth import get_user_model
from users.permissions import IsOrganization, IsAdminOffice, IsAteneoUser
from unittest.mock import MagicMock

User = get_user_model()


class RolePermissionTests(TestCase):

    def setUp(self):
        # Create org user
        self.org_user = User.objects.create_user(
            username='orguser',
            email='orguser@student.ateneo.edu',
            password='testpass123',
            role=User.Role.ORGANIZATION
        )

        # Create admin office user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='adminuser@ateneo.edu',
            password='testpass123',
            role=User.Role.ADMIN_OFFICE
        )

    def _mock_request(self, user):
        request = MagicMock()
        request.user = user
        return request

    def test_org_user_passes_IsOrganization(self):
        perm = IsOrganization()
        request = self._mock_request(self.org_user)
        self.assertTrue(perm.has_permission(request, None))

    def test_admin_user_fails_IsOrganization(self):
        perm = IsOrganization()
        request = self._mock_request(self.admin_user)
        self.assertFalse(perm.has_permission(request, None))

    def test_admin_user_passes_IsAdminOffice(self):
        perm = IsAdminOffice()
        request = self._mock_request(self.admin_user)
        self.assertTrue(perm.has_permission(request, None))

    def test_org_user_fails_IsAdminOffice(self):
        perm = IsAdminOffice()
        request = self._mock_request(self.org_user)
        self.assertFalse(perm.has_permission(request, None))

    def test_both_users_pass_IsAteneoUser(self):
        perm = IsAteneoUser()
        self.assertTrue(perm.has_permission(self._mock_request(self.org_user), None))
        self.assertTrue(perm.has_permission(self._mock_request(self.admin_user), None))