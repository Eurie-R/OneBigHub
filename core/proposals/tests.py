from django.test import TestCase, Client
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from datetime import timedelta

from .models import Proposal, Attachment

User = get_user_model()


# Helper Functions
def make_datetime(offset_hours=0):
    return timezone.now() + timedelta(hours=offset_hours)

def make_org_user(email='org@student.ateneo.edu', password='testpass123'):
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        role=User.Role.ORGANIZATION
    )
    return user

def make_proposal(org, status=Proposal.Status.DRAFT, **kwargs):
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
    def setUp(self):
        self.client = Client()
        self.user = make_org_user()
        self.org = self.user.org_profile
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


class ProposalSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.no_org_user = User.objects.create_user(
            username='no_org', email='no_org@test.com', password='pass'
        )
        self.client.login(email='no_org@test.com', password='pass')

    def test_create_proposal_without_org_redirects(self):
        """User without Org Profile should be kicked out of the create view."""
        try:
            self.client.get(reverse('proposals:create_proposal'))
        except NoReverseMatch as e:
            self.assertIn("'dashboard'", str(e))


class ProposalCreateViewTest(ProposalViewSetup):
    
    def test_save_draft_success(self):
        """Saving a draft does not require attachments and sets status to DRAFT."""
        data = self._post_data(action='draft')
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        proposal = Proposal.objects.first()
        self.assertRedirects(response, reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertEqual(Proposal.objects.count(), 1)
        self.assertEqual(proposal.status, Proposal.Status.DRAFT)

    def test_submit_without_attachment_fails(self):
        """Submitting an official proposal requires at least one attachment."""
        data = self._post_data(action='submit')
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Proposal.objects.count(), 0)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("must upload at least one supporting document" in str(m) for m in messages))

    def test_submit_with_attachment_success(self):
        """Submitting with an attachment saves as SUBMITTED."""
        data = self._post_data(action='submit')
        data['attachments'] = make_small_file()
        
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        proposal = Proposal.objects.first()
        self.assertRedirects(response, reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertEqual(proposal.status, Proposal.Status.SUBMITTED)
        self.assertEqual(Attachment.objects.count(), 1)


class ProposalValidationTest(ProposalViewSetup):

    def test_end_date_before_start_date_fails(self):
        """Tests the time-travel logic in forms.py clean()."""
        data = self._post_data(action='draft', start_offset=4, end_offset=2)
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'end_datetime', 'End time must be after start time.')

    def test_overlapping_submitted_proposal_fails(self):
        """Tests that double-booking an existing SUBMITTED slot is blocked."""
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, start_datetime=make_datetime(2), end_datetime=make_datetime(4))
        
        data = self._post_data(action='draft', start_offset=2, end_offset=4)
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'This time slot has already been booked by another proposal.')

    def test_overlapping_draft_proposal_succeeds(self):
        """Tests that drafts do NOT block time slots."""
        make_proposal(self.org, status=Proposal.Status.DRAFT, start_datetime=make_datetime(2), end_datetime=make_datetime(4))
        
        data = self._post_data(action='draft', start_offset=2, end_offset=4)
        response = self.client.post(reverse('proposals:create_proposal'), data)
        
        self.assertEqual(Proposal.objects.count(), 2)


class ProposalEditViewTest(ProposalViewSetup):
    def setUp(self):
        super().setUp()
        self.draft = make_proposal(self.org, status=Proposal.Status.DRAFT)
        self.edit_url = reverse('proposals:edit_proposal', args=[self.draft.pk])

    def test_cannot_edit_submitted_proposal(self):
        """Users cannot edit a proposal once it is submitted."""
        submitted_proposal = make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        url = reverse('proposals:edit_proposal', args=[submitted_proposal.pk])
        
        response = self.client.get(url)
        self.assertRedirects(response, reverse('proposals:proposal_detail', args=[submitted_proposal.pk]))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You can only edit draft proposals." in str(m) for m in messages))

    def test_submit_draft_without_any_files_fails(self):
        """Editing a draft and hitting submit fails if there are no old or new files."""
        data = self._post_data(action='submit')
        response = self.client.post(self.edit_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Proposal.Status.DRAFT) 
        
    def test_submit_draft_with_existing_files_succeeds(self):
        """Hitting submit on a draft works if it already had files attached previously."""
        Attachment.objects.create(proposal=self.draft, file=make_small_file())
        
        data = self._post_data(action='submit')
        response = self.client.post(self.edit_url, data)
        
        self.draft.refresh_from_db()
        self.assertRedirects(response, reverse('proposals:proposal_detail', args=[self.draft.pk]))
        self.assertEqual(self.draft.status, Proposal.Status.SUBMITTED)