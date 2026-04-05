from django.shortcuts import render, redirect
from .models import Venue, ReservationModel
from django.contrib.auth.decorators import login_required
from .forms import ReservationRequest

def venue_list(request):
    type_one_venues = Venue.objects.filter(venue_type = "1")
    type_two_venues = Venue.objects.filter(venue_type = "2")
    return render(request, 'venue_list.html', { "type_one_venues": type_one_venues, "type_two_venues": type_two_venues})

@login_required
def reservation_request(request, venue_id):
    venue = Venue.objects.get(id=venue_id)
    if request.method == 'POST':
        form = ReservationRequest(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.venue = venue   
            reservation.save()
            return redirect('venue_list')
    else:
        form = ReservationRequest()
    return render(request, 'reservation_request.html', {'form': form})

def avail_calendar(request, venue_id):
    venues = Venue.objects.get(id=venue_id)
    reservations = ReservationModel.objects.filter(venue=venues)
    return render(request, 'avail_calendar.html', {"venues": venues, "reservations": reservations})


