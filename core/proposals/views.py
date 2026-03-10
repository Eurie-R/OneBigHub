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
            
            if action == 'submit':
                proposal.status = Proposal.Status.SUBMITTED
                messages.success(request, "Proposal submitted successfully for review!") # REQ-12
            else:
                proposal.status = Proposal.Status.DRAFT
                messages.success(request, "Draft saved successfully.")
                
            proposal.save()

            # REQ-3 & REQ-5: Handle multiple file uploads
            for f in request.FILES.getlist('attachments'):
                Attachment.objects.create(proposal=proposal, file=f)

            return redirect('dashboard')
        else:
            # REQ-7 & REQ-11: If form is invalid display errors
            messages.error(request, "Please correct the errors below.")
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
            
            if action == 'submit':
                proposal.status = Proposal.Status.SUBMITTED
                messages.success(request, "Proposal submitted successfully for review!")
            else:
                proposal.status = Proposal.Status.DRAFT
                messages.success(request, "Draft updated successfully.")
                
            proposal.save()

            # Handle new attachments
            from .models import Attachment
            for f in request.FILES.getlist('attachments'):
                Attachment.objects.create(proposal=proposal, file=f)

            return redirect('admin:index')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Load the draft data
        form = ProposalForm(instance=proposal)

    return render(request, 'proposals/create_proposal.html', {'form': form, 'edit_mode': True})