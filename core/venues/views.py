from django.shortcuts import render, redirect, get_object_or_404
from .models import Venue, ReservationModel, ReservationRequest
from django.contrib.auth.decorators import login_required
from .forms import ReservationRequestForm
from proposals.models import Proposal
from users.models import AdminOfficeProfile
from django.contrib import messages
from django.views.decorators.http import require_POST

@login_required
def venue_type_choice(request):
    return render(request, 'venues/venue_type_choice.html')

@login_required
def type_1_list(request):
    type_one_venues = Venue.objects.filter(venue_type = "1")
    return render(request, 'venues/type_1_list.html', { "type_one_venues": type_one_venues })

@login_required
def type_2_list(request):
    type_two_venues = Venue.objects.filter(venue_type = "2")
    if has_approved_ppf(request):
        return render(request, 'venues/type_2_list.html', { "type_two_venues": type_two_venues })
    else:
        messages.error(request, "Must have approved PPF to reserve a type 2 venue.")
        return redirect('proposals:create_proposal')


@login_required
def reservation_request(request, venue_id):
    venue = Venue.objects.get(id=venue_id)
    if request.method == 'POST':
        reservation = ReservationRequest(venue=venue)
        form = ReservationRequestForm(request.POST, instance = reservation)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.venue = venue
            reservation.save()
            messages.success(request, "Reservation successfully submitted!")
            return redirect('venues:venue_type_choice')
    else:
        form = ReservationRequestForm()
    return render(request, 'venues/reservation_request.html', { 'venue': venue, 'form': form })

def has_approved_ppf(request):
    try:
        org_profile = request.user.org_profile
    except AttributeError:
        messages.error(request, "You must be linked to an organization.")
        return False
    approved = Proposal.objects.filter(organization=org_profile, status=Proposal.Status.APPROVED)
    return approved.exists()

@login_required
def avail_calendar(request, venue_id):
    venues = Venue.objects.get(id=venue_id)
    reservations = ReservationModel.objects.filter(venue=venues, status=ReservationModel.BOOKED)
    return render(request, 'venues/avail_calendar.html', {"venues": venues, "reservations": reservations})

@login_required
def review_reservations(request):
    try:
        admin_profile = request.user.admin_profile
    except AdminOfficeProfile.DoesNotExist:
        messages.error(request, "You must be an admin office user to review reservations.")
        return redirect('venues:venue_type_choice')
    
    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        action = request.POST.get('action')
        res_request = get_object_or_404(ReservationRequest, id=reservation_id)

        if action == 'approve':
            ReservationModel.objects.create(
                venue = res_request.venue,
                date = res_request.date,
                start = res_request.start,
                end = res_request.end,
                status = ReservationModel.BOOKED
            )
            messages.success(request, "Reservation Approved!")
        elif action == 'reject':
            ReservationModel.objects.create(
                venue = res_request.venue,
                date = res_request.date,
                start = res_request.start,
                end = res_request.end,
                status = ReservationModel.REJECTED
            )
            messages.success(request, "Reservation Rejected.")
        res_request.delete()
        
        return redirect('venues:review_reservations')

    pending_reservations = ReservationRequest.objects.all()
    return render(request, 'venues/review_reservations.html', {"reservations": pending_reservations})

@login_required
def public_reservations(request):
    approved = ReservationModel.objects.filter(status=ReservationModel.BOOKED)
    pending = ReservationRequest.objects.all()
    return render(request, 'venues/public_reservations.html', {"approved": approved, "pending": pending})
