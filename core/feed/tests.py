from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
 
from django.contrib.auth import get_user_model
from users.models import OrganizationProfile
from .models import Post
 
User = get_user_model()
 
 
# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def make_org_user(email, org_name):
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password='testpass123',
        role=User.Role.ORGANIZATION,
    )
    # Signal already created the profile — just update and return it
    org = user.org_profile
    org.org_name = org_name
    org.contact_email = email
    org.moderator_name = 'Test Mod'
    org.building = 'Main'
    org.room_number = '101'
    org.save()
    return user, org
 
 
def make_admin_user(email):
    return User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password='testpass123',
        role=User.Role.ADMIN_OFFICE,
    )
 
 
# ─────────────────────────────────────────────
# Model Tests
# ─────────────────────────────────────────────
 
class PostModelTest(TestCase):
 
    def setUp(self):
        self.user, self.org = make_org_user('orgA@ateneo.edu', 'Org A')
 
    def test_post_str(self):
        post = Post.objects.create(
            organization=self.org,
            title='Annual Gala',
            body='Join us for the Annual Gala!',
        )
        self.assertIn('Org A', str(post))
        self.assertIn('Annual Gala', str(post))
 
    def test_ordering_newest_first(self):
        import time
        p1 = Post.objects.create(organization=self.org, title='Old Post', body='...')
        time.sleep(0.01)  # ensure different timestamps
        p2 = Post.objects.create(organization=self.org, title='New Post', body='...')
        posts = list(Post.objects.all())
        self.assertEqual(posts[0].pk, p2.pk)
 
 
# ─────────────────────────────────────────────
# HTML View Tests
# ─────────────────────────────────────────────
 
class FeedHTMLTest(TestCase):
 
    def setUp(self):
        self.client = Client()
        self.user_a, self.org_a = make_org_user('orgA@ateneo.edu', 'Org A')
        self.user_b, self.org_b = make_org_user('orgB@ateneo.edu', 'Org B')
        self.admin_user = make_admin_user('admin@ateneo.edu')
 
        self.post_a = Post.objects.create(
            organization=self.org_a,
            title='Org A Event',
            body='Org A is hosting an event.',
            event_start=timezone.now() + timedelta(days=3),
            event_end=timezone.now() + timedelta(days=3, hours=2),
            location='Covered Courts',
        )
 
    def test_feed_list_redirects_unauthenticated(self):
        response = self.client.get(reverse('feed:feed_list'))
        self.assertEqual(response.status_code, 302)
 
    def test_feed_list_renders_for_authenticated_user(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('feed:feed_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Org A Event')
 
    def test_feed_detail_renders(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('feed:feed_detail', args=[self.post_a.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Covered Courts')
 
    def test_create_post_get_denied_for_non_org(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('feed:feed_create'))
        self.assertEqual(response.status_code, 302)
 
    def test_create_post_get_allowed_for_org(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse('feed:feed_create'))
        self.assertEqual(response.status_code, 200)
 
    def test_create_post_post_creates_post(self):
        self.client.force_login(self.user_a)
        response = self.client.post(reverse('feed:feed_create'), {
            'title': 'New Event',
            'body': 'Come join us!',
            'location': 'Rizal Library',
            'event_start': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'event_end':   (timezone.now() + timedelta(days=1, hours=2)).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(Post.objects.filter(title='New Event').count(), 1)
 
    def test_edit_post_denied_for_non_owner(self):
        self.client.force_login(self.user_b)
        response = self.client.post(reverse('feed:feed_edit', args=[self.post_a.pk]), {
            'title': 'Hijacked',
            'body': 'Should not save.',
        })
        self.assertEqual(response.status_code, 302)
        self.post_a.refresh_from_db()
        self.assertNotEqual(self.post_a.title, 'Hijacked')
 
    def test_delete_post_denied_for_non_owner(self):
        self.client.force_login(self.user_b)
        self.client.post(reverse('feed:feed_delete', args=[self.post_a.pk]))
        self.assertTrue(Post.objects.filter(pk=self.post_a.pk).exists())
 
    def test_delete_post_allowed_for_owner(self):
        self.client.force_login(self.user_a)
        self.client.post(reverse('feed:feed_delete', args=[self.post_a.pk]))
        self.assertFalse(Post.objects.filter(pk=self.post_a.pk).exists())
 
 
# ─────────────────────────────────────────────
# API Tests
# ─────────────────────────────────────────────
 
class FeedAPITest(TestCase):
 
    def setUp(self):
        self.client = APIClient()
        self.user_a, self.org_a = make_org_user('orgA@ateneo.edu', 'Org A')
        self.user_b, self.org_b = make_org_user('orgB@ateneo.edu', 'Org B')
        self.admin_user = make_admin_user('admin@ateneo.edu')
 
        self.post_a = Post.objects.create(
            organization=self.org_a,
            title='Org A Event',
            body='Org A is hosting an event.',
            event_start=timezone.now() + timedelta(days=3),
            event_end=timezone.now() + timedelta(days=3, hours=2),
            location='Covered Courts',
        )
        self.post_b = Post.objects.create(
            organization=self.org_b,
            title='Org B Workshop',
            body='Join our workshop!',
        )
 
    def test_api_feed_list_requires_authentication(self):
        response = self.client.get(reverse('feed:post_list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_api_feed_list_returns_all_posts(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(reverse('feed:post_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
 
    def test_api_feed_list_chronological_order(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('feed:post_list'))
        ids = [item['id'] for item in response.data]
        self.assertEqual(ids[0], self.post_b.pk)
 
    def test_api_feed_list_filter_by_org(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(reverse('feed:post_list') + f'?org={self.org_a.pk}')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['organization']['org_name'], 'Org A')
 
    def test_api_org_can_create_post(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'title': 'New Event',
            'body': 'Come and join us!',
            'location': 'Rizal Library',
            'event_start': (timezone.now() + timedelta(days=1)).isoformat(),
            'event_end': (timezone.now() + timedelta(days=1, hours=3)).isoformat(),
        }
        response = self.client.post(reverse('feed:post_create'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['organization']['org_name'], 'Org A')
 
    def test_api_admin_cannot_create_post(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(reverse('feed:post_create'), {'title': 'X', 'body': 'Y'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_api_event_end_before_start_fails(self):
        self.client.force_authenticate(user=self.user_a)
        now = timezone.now()
        payload = {
            'title': 'Bad Dates', 'body': '...',
            'event_start': (now + timedelta(days=2)).isoformat(),
            'event_end':   (now + timedelta(days=1)).isoformat(),
        }
        response = self.client.post(reverse('feed:post_create'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
 
    def test_api_post_detail_visible_to_all(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(reverse('feed:post_detail_api', args=[self.post_a.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location'], 'Covered Courts')
 
    def test_api_org_can_update_own_post(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.put(
            reverse('feed:post_detail_api', args=[self.post_a.pk]),
            {'title': 'Updated Title'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
 
    def test_api_org_cannot_update_another_orgs_post(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.put(
            reverse('feed:post_detail_api', args=[self.post_a.pk]),
            {'title': 'Hijacked'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
 
    def test_api_org_can_delete_own_post(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(reverse('feed:post_detail_api', args=[self.post_a.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post_a.pk).exists())
 
    def test_api_org_cannot_delete_another_orgs_post(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.delete(reverse('feed:post_detail_api', args=[self.post_a.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)