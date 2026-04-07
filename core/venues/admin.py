from django.contrib import admin
from .models import Venue, ReservationRequest, ReservationModel
# Register your models here.

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ["name", "venue_type", "description"]

@admin.register(ReservationRequest)
class ReservationRequestModel(admin.ModelAdmin):
    list_display = ["venue", "first_name", "date", "start", "end"]
