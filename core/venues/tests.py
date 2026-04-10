from django.test import TestCase
from django.urls import reverse, resolve
from .models import ReservationModel, Venue, ReservationRequest
from django.contrib.auth import get_user_model
from .views import venue_type_choice, type_1_list, type_2_list
from django.core.exceptions import ValidationError
from datetime import timedelta, date
User = get_user_model()

def make_valid_user(email='login@student.ateneo.edu', password='1234567ab'):
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        role=User.Role.ORGANIZATION
        )
    return user

#Models Tests
class VenueTestCase(TestCase):
    def setUp(self):
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.venue2 = Venue.objects.create(name="Blue Eagle Gym", venue_type="2", description="Ateneo's new and improved gymnasium that holds 7,000.")

#Check if venues can be correctly identified as type 1 or type 2
    def test_organize_by_type(self):
        self.assertEqual(self.venue1.venue_type, "1")
        self.assertEqual(self.venue2.venue_type, "2")

    def test_description_limit(self):
        self.assertLess(len(self.venue1.description), 256)
        self.assertLess(len(self.venue2.description), 256)

    def test_name_limit(self):
        self.assertLess(len(self.venue1.name), 256)
        self.assertLess(len(self.venue2.name), 256)

    def test_str_return(self):
        self.assertEqual(self.venue1.__str__(), "Colayco Pavillion")

class ReservationModelTestCase(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
    
    def test_default_pending(self):
        reservation = ReservationModel.objects.create(
            venue = self.venue,
            date = "2026-04-18",
            start = "10:00",
            end = "11:00"
        )
        self.assertEqual(reservation.status, ReservationModel.PENDING)

    def test_str_return(self):
        reservation = ReservationModel.objects.create(
            venue = self.venue,
            date = "2026-04-18",
            start = "10:00",
            end = "11:00"
        )
        self.assertEqual(reservation.__str__(), "Colayco Pavillion booked on 2026-04-18 from 10:00 - 11:00")

class ReservationRequestTestCase(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.resreq1 = ReservationRequest.objects.create(
            venue = self.venue,
            first_name = "John",
            last_name = "Smith",
            contact_number = "09209881745",
            email_address = "john12@gmail.com",
            purpose = "Hold meeting for ARSA.",
            pax = "12",
            date = "2026-05-04",
            start = "10:00",
            end = "11:00",
        )
    
    def test_number_limit(self):
        self.assertLess(len(self.resreq1.contact_number), 12)
    
    def test_str_return(self):
        self.assertEqual(self.resreq1.__str__(), "John Smith (09209881745) - Colayco Pavillion for 12 people")

    def test_invalid_time(self):
        self.invalid_time = ReservationRequest(
            venue = self.venue,
            first_name = "John",
            last_name = "Smith",
            contact_number = "09209881745",
            email_address = "john12@gmail.com",
            purpose = "Hold meeting for ARSA.",
            pax = "12",
            date = "2026-05-04",
            start = "11:00",
            end = "10:00",
        )
        with self.assertRaises(ValidationError) as cm:
            self.invalid_time.clean()
        exception = cm.exception
        self.assertIn('The reservation must end after the start time.', exception.messages)
    
    def test_invalid_date(self):
        self.invalid_date = ReservationRequest(
            venue = self.venue,
            first_name = "John",
            last_name = "Smith",
            contact_number = "09209881745",
            email_address = "john12@gmail.com",
            purpose = "Hold meeting for ARSA.",
            pax = "12",
            date = date.today() - timedelta(days=1) ,
            start = "10:00",
            end = "11:00",
        )
        with self.assertRaises(ValidationError) as cm:
            self.invalid_date.clean()
        exception = cm.exception
        self.assertIn('You cannot make a reservation before today.', exception.messages)
    
#Views Tests
class URLTestCase(TestCase):
    
    def setUp(self):
        self.user = make_valid_user()
        self.client.login(email= "login@student.ateneo.edu", password="1234567ab")
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.venue2 = Venue.objects.create(name="Blue Eagle Gym", venue_type="2", description="Ateneo's new and improved gymnasium that holds 7,000.")

    def test_venue_type_choice(self):
        path = reverse('venues:venue_type_choice')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_venue_1_list(self):
        path = reverse('venues:type_1_list')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    #Test redirect for no PPF
    def test_venue_2_list_no_PPF(self):
        path = reverse('venues:type_2_list')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    #Test redirect for not admin
    def test_review_reservations_not_admin(self):
        path = reverse('venues:review_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        
    def test_my_reservations(self):
        path = reverse('venues:my_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_reservation_request(self):
        path = reverse('venues:reservation_request', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_avail_calendar(self):
        path = reverse('venues:avail_calendar', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

class TemplateRendersTestCase(TestCase):
    def setUp(self):
        self.user = make_valid_user()
        self.client.login(email= "login@student.ateneo.edu", password="1234567ab")
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.venue2 = Venue.objects.create(name="Blue Eagle Gym", venue_type="2", description="Ateneo's new and improved gymnasium that holds 7,000.")

    def test_venue_type_choice_template(self):
        path = reverse('venues:venue_type_choice')
        response = self.client.get(path)
        self.assertTemplateUsed(response, 'venues/venue_type_choice.html')

    def test_venue_1_list_template(self):
        path = reverse('venues:type_1_list')
        response = self.client.get(path)
        self.assertTemplateUsed(response, 'venues/type_1_list.html')
        
    def test_my_reservations_template(self):
        path = reverse('venues:my_reservations')
        response = self.client.get(path)
        self.assertTemplateUsed(response, 'venues/my_reservations.html')

    def test_reservation_request_template(self):
        path = reverse('venues:reservation_request', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertTemplateUsed(response, 'venues/reservation_request.html')

    def test_avail_calendar_template(self):
        path = reverse('venues:avail_calendar', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertTemplateUsed(response, 'venues/avail_calendar.html')
