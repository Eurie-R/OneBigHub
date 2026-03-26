from django.shortcuts import render
from .models import Venue, Reservation

def venue_list(request):
    type_one_venues = Venue.objects.filter(venue_type = "1")
    type_two_venues = Venue.objects.filter(venue_type = "2")
    venues = Venue.objects.all()
    return render(request, 'venue_reservation.html', {"venues": venues})

