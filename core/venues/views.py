from django.shortcuts import render, redirect
from .models import Venue, ReservationModel, ReservationRequest
from django.contrib.auth.decorators import login_required
from .forms import ReservationRequestForm
from proposals.models import Proposal

def venue_list(request):
    type_one_venues = Venue.objects.filter(venue_type = "1")
    type_two_venues = Venue.objects.filter(venue_type = "2")
    return render(request, 'venues/venue_list.html', { "type_one_venues": type_one_venues, "type_two_venues": type_two_venues})

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
            return redirect('venues:venue_list')
    else:
        form = ReservationRequestForm()
    return render(request, 'venues/reservation_request.html', { 'venue': venue, 'form': form })

def has_approved_ppf(user):
    org_profile = user.org_profile
    approved = Proposal.objects.filter(organization=org_profile, status=Proposal.Status.APPROVED)
    return approved.exists()


def avail_calendar(request, venue_id):
    venues = Venue.objects.get(id=venue_id)
    reservations = ReservationModel.objects.filter(venue=venues)
    return render(request, 'venues/avail_calendar.html', {"venues": venues, "reservations": reservations})

