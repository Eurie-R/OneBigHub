from django.urls import path
from .views import venue_list, reservation_request, avail_calendar

app_name = 'venues'

urlpatterns = [
    path('', venue_list, name = 'venue_list'),
    path('<int:venue_id>/reservation/', reservation_request, name = 'reservation_request'),
    path('<int:venue_id>/availability/', avail_calendar, name = 'avail_calendar')
]