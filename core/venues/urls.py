from django.urls import path
from .views import venue_type_choice, reservation_request, avail_calendar, type_1_list, type_2_list, review_reservations, my_reservations

app_name = 'venues'

urlpatterns = [
    path('', venue_type_choice, name = 'venue_type_choice'),
    path('type/', venue_type_choice, name = 'venue_type_choice'),
    path('type1/', type_1_list, name = 'type_1_list'),
    path('type2/', type_2_list, name = 'type_2_list'),
    path('review/', review_reservations, name = 'review_reservations'),
    path('status/', my_reservations, name = 'my_reservations'),
    path('<int:venue_id>/reservation/', reservation_request, name = 'reservation_request'),
    path('<int:venue_id>/availability/', avail_calendar, name = 'avail_calendar')
]