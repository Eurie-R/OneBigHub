from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Proposal, Attachment
from .forms import ProposalForm


@login_required
def create_proposal(request):
    # Make sure the user has an organization profile (REQ-13)
    try:
        org_profile = request.user.org_profile
    except AttributeError:
        messages.error(request, "You must be linked to an Organization to submit a proposal.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProposalForm(request.POST)
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
                    return render(request, 'proposals/create_proposal.html', {'form': form})
                
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

            return redirect('admin:index')
    else:
        form = ProposalForm()

    return render(request, 'proposals/create_proposal.html', {'form': form})


@login_required
def edit_proposal(request, pk):
    # Check if user has an organization profile
    try:
        org_profile = request.user.org_profile
    except AttributeError:
        messages.error(request, "You must be linked to an Organization.")
        return redirect('admin:index')

    # Get the draft if it belongs to this user's organization
    proposal = get_object_or_404(Proposal, pk=pk, organization=org_profile)

    # Don't allow editing if its not a draft
    if proposal.status != Proposal.Status.DRAFT:
        messages.error(request, "You can only edit draft proposals.")
        return redirect('admin:index')

    if request.method == 'POST':
        form = ProposalForm(request.POST, instance=proposal)
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
                    return render(request, 'proposals/create_proposal.html', {'form': form, 'edit_mode': True})

                proposal.status = Proposal.Status.SUBMITTED
                messages.success(request, "Proposal submitted successfully for review!")
            else:
                proposal.status = Proposal.Status.DRAFT
                messages.success(request, "Draft updated successfully.")
                
            proposal.save()

            # Save any new attachments
            for f in new_files:
                Attachment.objects.create(proposal=proposal, file=f)

            return redirect('admin:index')
    else:
        # Load the draft data
        form = ProposalForm(instance=proposal)

    return render(request, 'proposals/create_proposal.html', {'form': form, 'edit_mode': True})