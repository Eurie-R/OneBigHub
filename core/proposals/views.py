from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Proposal
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
            return redirect('dashboard')
        else:
            # REQ-7 & REQ-11: If form is invalid display errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProposalForm()

    return render(request, 'proposals/create_proposal.html', {'form': form})