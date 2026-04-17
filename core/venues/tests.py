from django.test import TestCase
from django.urls import reverse, resolve
from .models import ReservationModel, Venue, ReservationRequest
from django.contrib.auth import get_user_model
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

def make_admin_user(email='admin@ateneo.edu', password='ab1234567'):
    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        role=User.Role.ADMIN_OFFICE
        )
    return user

#Models Tests
class VenueTestCase(TestCase):
    def setUp(self):
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.venue2 = Venue.objects.create(name="Blue Eagle Gym", venue_type="2", description="Ateneo's new and improved gymnasium that holds 7,000.")
        self.invalid_desc = Venue.objects.create(name="Blue Eagle Gym", venue_type="2", description="abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz")
        self.invalid_name = Venue.objects.create(name="abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz", venue_type="2", description="Ateneo's new and improved gymnasium that holds 7,000.")
        self.invalid_type = Venue.objects.create(name="Colayco Pavillion", venue_type="3", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
#Check if venues can be correctly identified as type 1 or type 2
    def test_organize_by_type(self):
        self.assertEqual(self.venue1.venue_type, "1")
        self.assertEqual(self.venue2.venue_type, "2")

    def test_description_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_desc.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 260).', exception.messages)

    def test_name_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_name.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 260).', exception.messages)

    def test_invalid_type(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_type.full_clean()
        exception = cm.exception
        self.assertIn("Value '3' is not a valid choice.", exception.messages)

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
            date = date.today(),
            start = "10:00",
            end = "11:00",
        )

        #Test for each field error
        self.invalid_resreq = ReservationRequest.objects.create(
            venue = self.venue,
            first_name = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz",
            last_name = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyza",
            contact_number = "092098817456",
            email_address = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzab",
            purpose = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabc",
            pax = "5",
            date = date.today(),
            start = "10:00",
            end = "11:00",
        )

        self.resmod1 = ReservationModel.objects.create(
            venue = self.venue,
            date = date.today(),
            start = "10:00",
            end = "11:00",
            status = ReservationModel.BOOKED
        )
    
    def test_number_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_resreq.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 11 characters (it has 12).', exception.messages)

    def test_first_name_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_resreq.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 260).', exception.messages)

    def test_last_name_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_resreq.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 261).', exception.messages)

    def test_email_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_resreq.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 262).', exception.messages)

    def test_purpose_limit(self):
        with self.assertRaises(ValidationError) as cm:
            self.invalid_resreq.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value has at most 255 characters (it has 263).', exception.messages)

    def test_pax(self):
        self.invalid_pax = ReservationRequest(
            venue = self.venue,
            first_name = "John",
            last_name = "Smith",
            contact_number = "09209881745",
            email_address = "john12@gmail.com",
            purpose = "Hold meeting for ARSA.",
            pax = -5,
            date = date.today(),
            start = "10:00",
            end = "11:00",
        )
        with self.assertRaises(ValidationError) as cm:
            self.invalid_pax.full_clean()
        exception = cm.exception
        self.assertIn('Ensure this value is greater than or equal to 0.', exception.messages)
    
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

    def test_double_book(self):
        self.invalid_book = ReservationRequest(
            venue = self.venue,
            first_name = "Jane",
            last_name = "Doe",
            contact_number = "09208765847",
            email_address = "jane12@gmail.com",
            purpose = "Hold meeting for CompSat.",
            pax = "21",
            date = date.today(),
            start = "10:00",
            end = "11:00",
        )
        with self.assertRaises(ValidationError) as cm:
            self.invalid_book.clean()
        exception = cm.exception
        self.assertIn('Sorry, there is a conflicting reservation. Please choose a different time or venue.', exception.messages)
    
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
        self.assertRedirects(response, reverse('proposals:create_proposal'))

    #Test redirect for not admin
    def test_review_reservations_not_admin(self):
        path = reverse('venues:review_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('venues:venue_type_choice'))

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

#Test that users who aren't logged in can't access pages
class LoggedOutUserTestCase(TestCase):
    def setUp(self):
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")

    def test_venue_type_choice_logged_out(self):
        path = reverse('venues:venue_type_choice')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_venue_1_list_logged_out(self):
        path = reverse('venues:type_1_list')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
    
    def test_venue_2_list_logged_out(self):
        path = reverse('venues:type_2_list')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_review_reservations_logged_out(self):
        path = reverse('venues:review_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_my_reservations_logged_out(self):
        path = reverse('venues:my_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_reservation_request_logged_out(self):
        path = reverse('venues:reservation_request', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

    def test_avail_calendar_logged_out(self):
        path = reverse('venues:avail_calendar', args=[self.venue1.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)

#Check for correct template redirect
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

#Check for correct post
class ReservationRequestPost(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.user = make_valid_user()
        self.client.login(email= "login@student.ateneo.edu", password="1234567ab")

    def test_post_success(self):
        path = reverse('venues:reservation_request', args=[self.venue.id])
        fields = {
                "first_name" : "John",
                "last_name" : "Smith",
                "contact_number" : "09209881745",
                "email_address" : "john12@gmail.com",
                "purpose" : "Hold meeting for ARSA.",
                "pax" : "12",
                "date" : date.today(),
                "start" : "10:00",
                "end" : "11:00",
        }
        
        response = self.client.post(path, fields)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ReservationRequest.objects.count(), 1)
        self.assertRedirects(response, reverse('venues:venue_type_choice'))

    def test_post_fail(self):
        path = reverse('venues:reservation_request', args=[self.venue.id])
        fields = {
                "first_name" : "John",
                "last_name" : "Smith",
                "contact_number" : "09209881745",
                "email_address" : "john12@gmail.com",
                "purpose" : "Hold meeting for ARSA.",
                "pax" : "12",
                "date" : date.today(),
                "start" : "10:00",
                "end" : "9:00",
        }
        
        response = self.client.post(path, fields)
        #No redirect and no request created because form was invalid
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReservationRequest.objects.count(), 0)

class RequestReviewTestCase(TestCase):
    def setUp(self):
        self.user = make_admin_user()
        self.client.login(email='admin@ateneo.edu', password='ab1234567')
        self.venue1 = Venue.objects.create(name="Colayco Pavillion", venue_type="1", description="Colayco Pavillion is a roofed but semi-outdoor venue with a capacity of 50.")
        self.req = ReservationRequest.objects.create(
            venue = self.venue1,
            first_name = "John",
            last_name = "Smith",
            contact_number = "09209881745",
            email_address = "john12@gmail.com",
            purpose = "Hold meeting for ARSA.",
            pax = "12",
            date = date.today(),
            start = "10:00",
            end = "11:00",
        )
    def test_admin_can_review(self):
        path = reverse('venues:review_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_review(self):
        self.user = make_valid_user()
        self.client.login(email='login@student.ateneo.edu', password='1234567ab')
        path = reverse('venues:review_reservations')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
    
    def test_approved_request(self):
        path = reverse('venues:review_reservations')
        response = self.client.post(path, {"reservation_id": self.req.id, "action": "approve"})
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, "Approved")
    
    def test_rejected_request(self):
        path = reverse('venues:review_reservations')
        response = self.client.post(path, {"reservation_id": self.req.id, "action": "reject"})
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, "Rejected")








