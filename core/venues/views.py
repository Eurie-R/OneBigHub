from django.shortcuts import render, redirect
from .models import Venue, Reservation
from django.contrib.auth.decorators import login_required
from .forms import ReservationForm

def venue_list(request):
    type_one_venues = Venue.objects.filter(venue_type = "1")
    type_two_venues = Venue.objects.filter(venue_type = "2")
    return render(request, 'venue_reservation.html', {"type_one_venues": type_one_venues, "type_two_venues": type_two_venues})

@login_required
def make_reservation(request):
    form = ReservationForm()
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('venue_reservation', {'form':form})