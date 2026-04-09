from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from .models import Proposal, Attachment
from .forms import ProposalForm


@login_required
def create_proposal(request):
    # Make sure the user has an organization profile (REQ-13)
    try:
        org_profile = request.user.org_profile
    except AttributeError:
        messages.error(request, "You must be linked to an Organization to submit a proposal.")
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES)
        action = request.POST.get('action') # Either draft or submit

        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.organization = org_profile
            
            # Get the files they are uploading right now
            uploaded_files = request.FILES.getlist('attachments')
            
            # If they are submitting make sure there are files
            if action == 'submit':
                if not uploaded_files:
                    messages.error(request, "You must upload at least one supporting document to submit.")
                    return render(request, 'proposals/create_proposal.html', {
                        'form': form,
                        'current_page': 'proposals'
                    })
                
                proposal.status = Proposal.Status.SUBMITTED
                messages.success(request, "Proposal submitted successfully for review!")
            else:
                proposal.status = Proposal.Status.DRAFT
                messages.success(request, "Draft saved successfully.")
                
            proposal.save()

            # Save the attachments
            from .models import Attachment
            for f in uploaded_files:
                Attachment.objects.create(proposal=proposal, file=f)

            return redirect('proposals:proposal_detail', pk=proposal.pk)
    else:
        form = ProposalForm()

    return render(request, 'proposals/create_proposal.html', {
        'form': form,
        'current_page': 'proposals'
    })


@login_required
def edit_proposal(request, pk):
    # Check if user has an organization profile
    try:
        org_profile = request.user.org_profile
    except AttributeError:
        messages.error(request, "You must be linked to an Organization.")
        return redirect('users:dashboard')

    # Get the draft if it belongs to this user's organization
    proposal = get_object_or_404(Proposal, pk=pk, organization=org_profile)

    # Don't allow editing if its not a draft
    if proposal.status != Proposal.Status.DRAFT:
        messages.error(request, "You can only edit draft proposals.")
        return redirect('proposals:proposal_detail', pk=proposal.pk)

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES, instance=proposal)
        action = request.POST.get('action')

        if form.is_valid():
            proposal = form.save(commit=False)
            
            # Get any new files they are uploading right now
            new_files = request.FILES.getlist('attachments')
            from .models import Attachment # Import here to use for the check
            
            if action == 'submit':
                # Check if they have new files or if the database already has files from before
                has_existing_files = Attachment.objects.filter(proposal=proposal).exists()
                
                if not new_files and not has_existing_files:
                    messages.error(request, "You must upload at least one supporting document to submit.")
                    return render(request, 'proposals/create_proposal.html', {
                        'form': form,
                        'edit_mode': True,
                        'current_page': 'proposals'
                    })

                proposal.status = Proposal.Status.SUBMITTED
                messages.success(request, "Proposal submitted successfully for review!")
            else:
                proposal.status = Proposal.Status.DRAFT
                messages.success(request, "Draft updated successfully.")
                
            proposal.save()

            # Save any new attachments
            for f in new_files:
                Attachment.objects.create(proposal=proposal, file=f)

            return redirect('proposals:proposal_detail', pk=proposal.pk)
    else:
        # Load the draft data
        form = ProposalForm(instance=proposal)

    return render(request, 'proposals/create_proposal.html', {
        'form': form,
        'edit_mode': True,
        'current_page': 'proposals'
    })

@login_required
def proposal_detail(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    attachments = Attachment.objects.filter(proposal=proposal)
    return render(request, 'proposals/proposal_detail.html', {
        'proposal': proposal,
        'attachments': attachments,
        'current_page': 'proposals'
    })


@login_required
def proposal_list(request):
    if request.user.is_admin_office:
        try:
            admin_profile = request.user.admin_profile
        except AttributeError:
            messages.error(request, "You must have an admin office profile to view proposals.")
            return redirect('users:dashboard')
        # Show proposals directed to this office that need attention
        proposals = Proposal.objects.filter(
            reviewing_office=admin_profile.office_type
        ).exclude(status=Proposal.Status.DRAFT).order_by('-updated_at')
    elif request.user.is_org:
        try:
            org_profile = request.user.org_profile
        except AttributeError:
            messages.error(request, "You must be linked to an Organization.")
            return redirect('users:dashboard')
        proposals = Proposal.objects.filter(organization=org_profile).order_by('-updated_at')
    else:
        messages.error(request, "Access denied.")
        return redirect('users:dashboard')

    return render(request, 'proposals/proposal_list.html', {
        'proposals': proposals,
        'current_page': 'proposals',
    })


@login_required
@require_POST
def review_proposal(request, pk):
    # Only admin office users can review
    if not request.user.is_admin_office:
        messages.error(request, "Only administrative office users can review proposals.")
        return redirect('proposals:proposal_detail', pk=pk)

    try:
        admin_profile = request.user.admin_profile
    except AttributeError:
        messages.error(request, "You must have an admin office profile.")
        return redirect('proposals:proposal_detail', pk=pk)

    proposal = get_object_or_404(Proposal, pk=pk)

    # Ensure the proposal is directed to this office
    if proposal.reviewing_office != admin_profile.office_type:
        messages.error(request, "This proposal is not assigned to your office.")
        return redirect('proposals:proposal_detail', pk=pk)

    # Only allow reviewing SUBMITTED or UNDER_REVIEW proposals
    if proposal.status not in (Proposal.Status.SUBMITTED, Proposal.Status.UNDER_REVIEW):
        messages.error(request, "Only submitted proposals can be reviewed.")
        return redirect('proposals:proposal_detail', pk=pk)

    action = request.POST.get('action')
    review_comment = request.POST.get('review_comment', '').strip()

    if action == 'approve':
        proposal.status = Proposal.Status.APPROVED
        proposal.reviewed_by = admin_profile
        proposal.review_comment = review_comment
        proposal.save()
        messages.success(request, f"Proposal '{proposal.title}' has been approved.")
    elif action == 'reject':
        if not review_comment:
            messages.error(request, "A comment is required when rejecting a proposal.")
            return redirect('proposals:proposal_detail', pk=pk)
        proposal.status = Proposal.Status.REJECTED
        proposal.reviewed_by = admin_profile
        proposal.review_comment = review_comment
        proposal.save()
        messages.success(request, f"Proposal '{proposal.title}' has been rejected.")
    elif action == 'under_review':
        proposal.status = Proposal.Status.UNDER_REVIEW
        proposal.reviewed_by = admin_profile
        proposal.review_comment = review_comment
        proposal.save()
        messages.success(request, f"Proposal '{proposal.title}' is now under review.")
    else:
        messages.error(request, "Invalid action.")

    return redirect('proposals:proposal_detail', pk=pk)

@login_required
def proposal_status_api(request):
    """JSON endpoint for org dashboard live status polling."""
    if not request.user.is_org:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        org_profile = request.user.org_profile
    except AttributeError:
        return JsonResponse({'error': 'No org profile'}, status=400)

    proposals = Proposal.objects.filter(
        organization=org_profile
    ).order_by('-updated_at')[:10]

    counts = {
        'draft': 0, 'submitted': 0,
        'under_review': 0, 'approved': 0, 'rejected': 0,
    }
    for p in Proposal.objects.filter(organization=org_profile):
        key = p.status.lower()
        if key in counts:
            counts[key] += 1

    data = [{
        'id': p.pk,
        'title': p.title or 'Untitled Draft',
        'status': p.status,
        'status_display': p.get_status_display(),
        'reviewing_office': p.reviewing_office,
        'updated_at': p.updated_at.strftime('%b %d, %Y'),
    } for p in proposals]

    return JsonResponse({
        'proposals': data,
        'counts': counts,
        'timestamp': timezone.now().strftime('%b %d, %Y %I:%M %p'),
    })