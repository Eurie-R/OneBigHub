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

def make_admin_user(email='admin@ateneo.edu', password='testpass123', office_type='OSA'):
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        role=User.Role.ADMIN_OFFICE
    )
    profile = user.admin_profile
    profile.office_name = f'{office_type} Office'
    profile.office_type = office_type
    profile.contact_email = email
    profile.building = 'Admin Building'
    profile.room_number = '101'
    profile.save()
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


# ─────────────────────────────────────────────
# Proposal List View Tests
# ─────────────────────────────────────────────

class ProposalListOrgViewTest(ProposalViewSetup):
    """Org users see only their own proposals on the list page."""

    def test_list_page_returns_200(self):
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_page_uses_correct_template(self):
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertTemplateUsed(response, 'proposals/proposal_list.html')

    def test_org_sees_own_proposals(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        make_proposal(self.org, status=Proposal.Status.DRAFT)
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 2)

    def test_org_does_not_see_other_orgs_proposals(self):
        other_user = make_org_user(email='other@student.ateneo.edu')
        other_org = other_user.org_profile
        make_proposal(other_org, status=Proposal.Status.SUBMITTED)

        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 0)

    def test_empty_list_returns_200(self):
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['proposals']), 0)


class ProposalListAdminViewTest(TestCase):
    """Admin office users see proposals directed to their office (non-draft only)."""

    def setUp(self):
        self.client = Client()
        self.admin_user = make_admin_user(office_type='OSA')
        self.admin_profile = self.admin_user.admin_profile
        self.client.login(email='admin@ateneo.edu', password='testpass123')

        self.org_user = make_org_user()
        self.org = self.org_user.org_profile

    def test_admin_sees_submitted_proposals_for_their_office(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 1)

    def test_admin_does_not_see_drafts(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT, reviewing_office='OSA')
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 0)

    def test_admin_does_not_see_proposals_for_other_offices(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CFMO')
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 0)

    def test_admin_sees_under_review_and_decided_proposals(self):
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.REJECTED, reviewing_office='OSA')
        response = self.client.get(reverse('proposals:proposal_list'))
        self.assertEqual(len(response.context['proposals']), 3)


# ─────────────────────────────────────────────
# Admin Review Workflow Tests
# ─────────────────────────────────────────────

class AdminReviewWorkflowTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = make_admin_user(office_type='OSA')
        self.admin_profile = self.admin_user.admin_profile

        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.proposal = make_proposal(
            self.org,
            status=Proposal.Status.SUBMITTED,
            reviewing_office='OSA'
        )
        self.review_url = reverse('proposals:review_proposal', args=[self.proposal.pk])
        self.detail_url = reverse('proposals:proposal_detail', args=[self.proposal.pk])

        self.client.login(email='admin@ateneo.edu', password='testpass123')

    # --- Approve ---

    def test_approve_sets_status_to_approved(self):
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': 'Looks good.'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.APPROVED)

    def test_approve_saves_reviewed_by(self):
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.reviewed_by, self.admin_profile)

    def test_approve_saves_review_comment(self):
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': 'All good!'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.review_comment, 'All good!')

    def test_approve_without_comment_still_succeeds(self):
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.APPROVED)

    def test_approve_redirects_to_detail(self):
        response = self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.assertRedirects(response, self.detail_url)

    # --- Reject ---

    def test_reject_sets_status_to_rejected(self):
        self.client.post(self.review_url, {'action': 'reject', 'review_comment': 'Missing documents.'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.REJECTED)

    def test_reject_saves_review_comment(self):
        self.client.post(self.review_url, {'action': 'reject', 'review_comment': 'Missing documents.'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.review_comment, 'Missing documents.')

    def test_reject_without_comment_fails(self):
        """A rejection comment is mandatory."""
        self.client.post(self.review_url, {'action': 'reject', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertNotEqual(self.proposal.status, Proposal.Status.REJECTED)

    def test_reject_without_comment_shows_error_message(self):
        response = self.client.post(self.review_url, {'action': 'reject', 'review_comment': ''}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('comment is required' in m for m in msgs))

    def test_reject_redirects_to_detail(self):
        response = self.client.post(self.review_url, {'action': 'reject', 'review_comment': 'Reason.'})
        self.assertRedirects(response, self.detail_url)

    # --- Mark as Under Review ---

    def test_mark_under_review_sets_correct_status(self):
        self.client.post(self.review_url, {'action': 'under_review', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.UNDER_REVIEW)

    def test_can_approve_from_under_review(self):
        """A proposal that is UNDER_REVIEW can still be approved."""
        self.proposal.status = Proposal.Status.UNDER_REVIEW
        self.proposal.save()
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.APPROVED)

    def test_can_reject_from_under_review(self):
        """A proposal that is UNDER_REVIEW can still be rejected."""
        self.proposal.status = Proposal.Status.UNDER_REVIEW
        self.proposal.save()
        self.client.post(self.review_url, {'action': 'reject', 'review_comment': 'Not suitable.'})
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, Proposal.Status.REJECTED)


# ─────────────────────────────────────────────
# Admin Review Permission / Guard Tests
# ─────────────────────────────────────────────

class AdminReviewPermissionTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.proposal = make_proposal(
            self.org,
            status=Proposal.Status.SUBMITTED,
            reviewing_office='OSA'
        )
        self.review_url = reverse('proposals:review_proposal', args=[self.proposal.pk])
        self.detail_url = reverse('proposals:proposal_detail', args=[self.proposal.pk])

    def test_org_user_cannot_review(self):
        """An organization user should not be able to approve/reject."""
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertNotEqual(self.proposal.status, Proposal.Status.APPROVED)

    def test_org_user_review_shows_error_message(self):
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        response = self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('administrative office' in m for m in msgs))

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('/proposals/', response['Location'].split('?')[0])

    def test_wrong_office_cannot_review(self):
        """An admin from CFMO should not be able to review an OSA proposal."""
        cfmo_user = make_admin_user(email='cfmo@ateneo.edu', office_type='CFMO')
        self.client.login(email='cfmo@ateneo.edu', password='testpass123')
        self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''})
        self.proposal.refresh_from_db()
        self.assertNotEqual(self.proposal.status, Proposal.Status.APPROVED)

    def test_wrong_office_shows_error_message(self):
        cfmo_user = make_admin_user(email='cfmo@ateneo.edu', office_type='CFMO')
        self.client.login(email='cfmo@ateneo.edu', password='testpass123')
        response = self.client.post(self.review_url, {'action': 'approve', 'review_comment': ''}, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('not assigned to your office' in m for m in msgs))

    def test_cannot_review_a_draft(self):
        """Drafts are not in the review pipeline."""
        admin_user = make_admin_user(office_type='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        draft = make_proposal(self.org, status=Proposal.Status.DRAFT, reviewing_office='OSA')
        url = reverse('proposals:review_proposal', args=[draft.pk])
        self.client.post(url, {'action': 'approve', 'review_comment': ''})
        draft.refresh_from_db()
        self.assertEqual(draft.status, Proposal.Status.DRAFT)

    def test_cannot_review_already_approved_proposal(self):
        admin_user = make_admin_user(office_type='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        approved = make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        url = reverse('proposals:review_proposal', args=[approved.pk])
        self.client.post(url, {'action': 'reject', 'review_comment': 'Changed my mind.'})
        approved.refresh_from_db()
        self.assertEqual(approved.status, Proposal.Status.APPROVED)

    def test_review_endpoint_rejects_get_requests(self):
        """review_proposal is POST-only."""
        admin_user = make_admin_user(office_type='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, 405)


# ─────────────────────────────────────────────
# Review Feedback Display Tests
# ─────────────────────────────────────────────

class ReviewFeedbackDisplayTest(TestCase):
    """Ensure the detail page shows/hides the right UI elements for each role."""

    def setUp(self):
        self.client = Client()
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.admin_user = make_admin_user(office_type='OSA')

    def test_admin_review_panel_visible_to_admin_on_submitted_proposal(self):
        proposal = make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        response = self.client.get(reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertContains(response, 'Review This Proposal')

    def test_admin_review_panel_hidden_from_org_user(self):
        proposal = make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        response = self.client.get(reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertNotContains(response, 'Review This Proposal')

    def test_admin_review_panel_hidden_after_approval(self):
        proposal = make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        response = self.client.get(reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertNotContains(response, 'Review This Proposal')

    def test_office_feedback_section_shown_after_review(self):
        proposal = make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA',
                                  review_comment='Approved — all docs in order.',
                                  reviewed_by=self.admin_user.admin_profile)
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        response = self.client.get(reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertContains(response, 'Office Feedback')
        self.assertContains(response, 'Approved — all docs in order.')

    def test_office_feedback_section_hidden_when_no_review(self):
        proposal = make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        response = self.client.get(reverse('proposals:proposal_detail', args=[proposal.pk]))
        self.assertNotContains(response, 'Office Feedback')


# ─────────────────────────────────────────────
# Admin Tracking Dashboard Tests
# ─────────────────────────────────────────────

class AdminTrackingDashboardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = make_admin_user(email='admin@ateneo.edu', office_type='OSA')
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.url = reverse('proposals:admin_tracking_dashboard')
        self.client.login(email='admin@ateneo.edu', password='testpass123')

    # --- Access ---

    def test_returns_200_for_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'proposals/admin_tracking_dashboard.html')

    def test_org_user_is_redirected(self):
        self.client.logout()
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        response = self.client.get(self.url)
        self.assertRedirects(response, '/dashboard/')

    def test_unauthenticated_user_is_redirected(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    # --- Counts ---

    def test_counts_are_correct_for_office(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.REJECTED, reviewing_office='OSA')
        response = self.client.get(self.url)
        counts = response.context['counts']
        self.assertEqual(counts['submitted'], 2)
        self.assertEqual(counts['under_review'], 1)
        self.assertEqual(counts['approved'], 1)
        self.assertEqual(counts['rejected'], 1)
        self.assertEqual(counts['total'], 5)
        self.assertEqual(counts['pending'], 3)

    def test_drafts_are_excluded_from_counts(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT, reviewing_office='OSA')
        response = self.client.get(self.url)
        self.assertEqual(response.context['counts']['total'], 0)

    def test_other_office_proposals_excluded_from_counts(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CFMO')
        response = self.client.get(self.url)
        self.assertEqual(response.context['counts']['total'], 0)

    # --- Status filter ---

    def test_no_filter_returns_all_non_draft(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 2)

    def test_filter_by_submitted(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=SUBMITTED')
        self.assertEqual(len(response.context['proposals']), 1)
        self.assertEqual(response.context['status_filter'], 'SUBMITTED')

    def test_filter_by_approved(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=APPROVED')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_filter_by_rejected(self):
        make_proposal(self.org, status=Proposal.Status.REJECTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=REJECTED')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_filter_by_under_review(self):
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=UNDER_REVIEW')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_unknown_filter_returns_empty(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=BOGUS')
        self.assertEqual(len(response.context['proposals']), 0)

    def test_empty_filter_param_returns_all(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=')
        self.assertEqual(len(response.context['proposals']), 2)

    # --- Context ---

    def test_admin_profile_in_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['admin_profile'], self.admin_user.admin_profile)

    def test_page_shows_pipeline_bar_when_proposals_exist(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url)
        self.assertContains(response, 'Pipeline Overview')

    def test_page_hides_pipeline_bar_when_no_proposals(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Pipeline Overview')


# ─────────────────────────────────────────────
# Org Dashboard Proposal Status Section Tests
# ─────────────────────────────────────────────

class OrgDashboardProposalStatusTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.client.login(email='org@student.ateneo.edu', password='testpass123')
        self.url = '/dashboard/'

    # --- Counts ---

    def test_dashboard_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_proposal_counts_all_zero_with_no_proposals(self):
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(sum(counts.values()), 0)

    def test_proposal_counts_reflect_actual_statuses(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT)
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW)
        make_proposal(self.org, status=Proposal.Status.APPROVED)
        make_proposal(self.org, status=Proposal.Status.REJECTED)
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(counts['draft'], 1)
        self.assertEqual(counts['submitted'], 1)
        self.assertEqual(counts['under_review'], 1)
        self.assertEqual(counts['approved'], 1)
        self.assertEqual(counts['rejected'], 1)

    def test_counts_only_include_own_proposals(self):
        other_user = make_org_user(email='other@student.ateneo.edu')
        other_org = other_user.org_profile
        make_proposal(other_org, status=Proposal.Status.APPROVED)
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(sum(counts.values()), 0)

    # --- Recent proposals ---

    def test_recent_proposals_in_context(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        response = self.client.get(self.url)
        self.assertIn('recent_proposals', response.context)
        self.assertEqual(len(response.context['recent_proposals']), 1)

    def test_recent_proposals_capped_at_five(self):
        for i in range(7):
            make_proposal(self.org, status=Proposal.Status.SUBMITTED, title=f'Proposal {i}')
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['recent_proposals']), 5)

    def test_recent_proposals_not_from_other_orgs(self):
        other_user = make_org_user(email='other@student.ateneo.edu')
        make_proposal(other_user.org_profile, status=Proposal.Status.SUBMITTED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['recent_proposals']), 0)

    # --- Template rendering ---

    def test_status_cards_rendered_for_org(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'id="count-draft"')
        self.assertContains(response, 'id="count-submitted"')
        self.assertContains(response, 'id="count-approved"')
        self.assertContains(response, 'id="count-rejected"')

    def test_live_update_script_present_for_org(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'pollProposalStatus')
        self.assertContains(response, 'setInterval')


class AdminDashboardProposalStatusTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = make_admin_user(email='admin@ateneo.edu', office_type='OSA')
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        self.url = '/dashboard/'

    def test_dashboard_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_proposal_counts_in_context(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.REJECTED, reviewing_office='OSA')
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(counts['submitted'], 1)
        self.assertEqual(counts['under_review'], 1)
        self.assertEqual(counts['approved'], 1)
        self.assertEqual(counts['rejected'], 1)
        self.assertEqual(counts['pending'], 2)

    def test_drafts_excluded_from_admin_counts(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT, reviewing_office='OSA')
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(counts['pending'], 0)

    def test_other_office_proposals_excluded(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CFMO')
        response = self.client.get(self.url)
        counts = response.context['proposal_counts']
        self.assertEqual(counts['pending'], 0)

    def test_recent_proposals_include_org_name(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url)
        self.assertIn('recent_proposals', response.context)
        self.assertEqual(len(response.context['recent_proposals']), 1)

    def test_live_update_script_absent_for_admin(self):
        """Admins use a static page load, no JS polling needed."""
        response = self.client.get(self.url)
        self.assertNotContains(response, 'pollProposalStatus')


# ─────────────────────────────────────────────
# Proposal Status JSON API Tests
# ─────────────────────────────────────────────

class ProposalStatusAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.url = reverse('proposals:proposal_status_api')
        self.client.login(email='org@student.ateneo.edu', password='testpass123')

    # --- Access ---

    def test_returns_200_for_org_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_returns_json(self):
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_admin_user_gets_403(self):
        self.client.logout()
        make_admin_user(email='admin@ateneo.edu', office_type='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_is_redirected(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    # --- Response shape ---

    def test_response_contains_expected_keys(self):
        response = self.client.get(self.url)
        data = response.json()
        self.assertIn('proposals', data)
        self.assertIn('counts', data)
        self.assertIn('timestamp', data)

    def test_counts_keys_present(self):
        response = self.client.get(self.url)
        counts = response.json()['counts']
        for key in ('draft', 'submitted', 'under_review', 'approved', 'rejected'):
            self.assertIn(key, counts)

    def test_proposal_entry_has_required_fields(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        response = self.client.get(self.url)
        entry = response.json()['proposals'][0]
        for field in ('id', 'title', 'status', 'status_display', 'reviewing_office', 'updated_at'):
            self.assertIn(field, entry)

    # --- Data correctness ---

    def test_counts_match_actual_proposal_statuses(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT)
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        make_proposal(self.org, status=Proposal.Status.APPROVED)
        response = self.client.get(self.url)
        counts = response.json()['counts']
        self.assertEqual(counts['draft'], 1)
        self.assertEqual(counts['submitted'], 1)
        self.assertEqual(counts['approved'], 1)

    def test_proposals_capped_at_ten(self):
        for i in range(12):
            make_proposal(self.org, status=Proposal.Status.SUBMITTED, title=f'Proposal {i}')
        response = self.client.get(self.url)
        self.assertLessEqual(len(response.json()['proposals']), 10)

    def test_only_own_proposals_returned(self):
        other_user = make_org_user(email='other@student.ateneo.edu')
        make_proposal(other_user.org_profile, status=Proposal.Status.SUBMITTED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.json()['proposals']), 0)
        self.assertEqual(sum(response.json()['counts'].values()), 0)

    def test_status_display_is_human_readable(self):
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW)
        response = self.client.get(self.url)
        entry = response.json()['proposals'][0]
        self.assertEqual(entry['status_display'], 'Under Review')

    def test_empty_response_when_no_proposals(self):
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(data['proposals'], [])
        self.assertEqual(sum(data['counts'].values()), 0)


# ─────────────────────────────────────────────
# Public Proposals Listing Tests
# ─────────────────────────────────────────────

class PublicProposalsListingTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.org_user = make_org_user()
        self.org = self.org_user.org_profile
        self.url = reverse('proposals:public_proposals')
        self.client.login(email='org@student.ateneo.edu', password='testpass123')

    # --- Access ---

    def test_returns_200_for_org_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_returns_200_for_admin_user(self):
        self.client.logout()
        make_admin_user(email='admin@ateneo.edu', office_type='OSA')
        self.client.login(email='admin@ateneo.edu', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_is_redirected(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'proposals/public_proposals.html')

    # --- Visibility rules ---

    def test_drafts_are_not_shown(self):
        make_proposal(self.org, status=Proposal.Status.DRAFT)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 0)

    def test_submitted_proposals_are_shown(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 1)

    def test_under_review_proposals_are_shown(self):
        make_proposal(self.org, status=Proposal.Status.UNDER_REVIEW)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 1)

    def test_approved_proposals_are_shown(self):
        make_proposal(self.org, status=Proposal.Status.APPROVED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 1)

    def test_rejected_proposals_are_shown(self):
        make_proposal(self.org, status=Proposal.Status.REJECTED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 1)

    def test_proposals_from_all_orgs_are_shown(self):
        other_user = make_org_user(email='other@student.ateneo.edu')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED)
        make_proposal(other_user.org_profile, status=Proposal.Status.APPROVED)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 2)

    # --- Office filter ---

    def test_filter_by_office_returns_only_matching_proposals(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CFMO')
        response = self.client.get(self.url + '?office=OSA')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_office_filter_value_in_context(self):
        response = self.client.get(self.url + '?office=CFMO')
        self.assertEqual(response.context['office_filter'], 'CFMO')

    def test_no_office_filter_returns_all_offices(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CFMO')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='CSMO')
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['proposals']), 3)

    # --- Status filter ---

    def test_filter_by_status_approved(self):
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=APPROVED')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_filter_by_status_submitted(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.REJECTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?status=SUBMITTED')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_status_filter_value_in_context(self):
        response = self.client.get(self.url + '?status=REJECTED')
        self.assertEqual(response.context['status_filter'], 'REJECTED')

    # --- Combined filters ---

    def test_office_and_status_filter_combined(self):
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='OSA')
        make_proposal(self.org, status=Proposal.Status.APPROVED, reviewing_office='CFMO')
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?office=OSA&status=APPROVED')
        self.assertEqual(len(response.context['proposals']), 1)

    def test_filter_with_no_matches_returns_empty(self):
        make_proposal(self.org, status=Proposal.Status.SUBMITTED, reviewing_office='OSA')
        response = self.client.get(self.url + '?office=CFMO&status=APPROVED')
        self.assertEqual(len(response.context['proposals']), 0)

    # --- Context ---

    def test_office_choices_in_context(self):
        response = self.client.get(self.url)
        self.assertIn('office_choices', response.context)

    def test_status_choices_in_context(self):
        response = self.client.get(self.url)
        self.assertIn('status_choices', response.context)