from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from datetime import timedelta
 
from .models import Proposal, Attachment

 
User = get_user_model()

def make_datetime(offset_hours=0):
    """Return a timezone-aware datetime offset from now."""
    return timezone.now() + timedelta(hours=offset_hours)
 
 
def make_org_user(email='org@student.ateneo.edu', password='testpass123'):
    """
    Create a User with the ORGANIZATION role.
    """
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        role=User.Role.ORGANIZATION
    )
    return user
 
 
def make_proposal(org, status=Proposal.Status.DRAFT, **kwargs):
    """Factory helper to create a Proposal with a real OrganizationProfile."""
    defaults = dict(
        title='Test Proposal',
        nature_of_activity='Workshop',
        target_attendees='Students',
        objectives='Learn things',
        start_datetime=make_datetime(2),
        end_datetime=make_datetime(4),
        reviewing_office='OSA',
        status=status,
        organization=org,
    )
    defaults.update(kwargs)
    return Proposal.objects.create(**defaults)
 
 
def make_small_file(name='doc.pdf', content=b'PDF content', content_type='application/pdf'):
    return SimpleUploadedFile(name, content, content_type=content_type)


class ProposalViewSetup(TestCase):
    """
    Base class for view tests.
    """
 
    def setUp(self):
        self.client = Client()
        self.user = make_org_user()
        self.org = self.user.org_profile  # created by signal in users/signals.py
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
 
    def _post_data(self, action='draft', start_offset=2, end_offset=4):
        return {
            'title': 'New Event',
            'nature_of_activity': 'Seminar',
            'target_attendees': 'Students',
            'objectives': 'Learn',
            'start_datetime': make_datetime(start_offset).strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': make_datetime(end_offset).strftime('%Y-%m-%dT%H:%M'),
            'reviewing_office': 'OSA',
            'action': action,
        }

class ProposalDetailViewTest(ProposalViewSetup):
 
    def setUp(self):
        super().setUp()
        self.proposal = make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        self.detail_url = reverse('proposals:proposal_detail', args=[self.proposal.pk])
 
    def test_detail_page_returns_200(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
 
    def test_detail_page_uses_correct_template(self):
        response = self.client.get(self.detail_url)
        self.assertTemplateUsed(response, 'proposals/proposal_detail.html')
 
    def test_detail_page_contains_proposal_title(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'Test Proposal')
 
    def test_detail_page_context_has_proposal(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.context['proposal'], self.proposal)
 
    def test_detail_page_contains_attachments(self):
        Attachment.objects.create(proposal=self.proposal, file=make_small_file())
        response = self.client.get(self.detail_url)
        self.assertEqual(len(response.context['attachments']), 1)
 
    def test_nonexistent_proposal_returns_404(self):
        response = self.client.get(reverse('proposals:proposal_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)
 