from django.test import TestCase
from .models import Reservation, Venue

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
