from django.db import models
from django.core.exceptions import ValidationError

class Venue(models.Model):
    ONE = "1"
    TWO = "2"

    #Two types of venues, classified by requirement of PPF
    VENUE_TYPES = (
    (ONE, "Type 1"),
    (TWO, "Type 2"),
    )

    name = models.CharField(max_length=255)
    venue_type = models.CharField(max_length=1, choices = VENUE_TYPES)
    description = models.CharField(max_length=255)
    

    def __str__(self):
        return self.name
    
class ReservationModel(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)

    #Time info
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()

        #Reservation Status
    BOOK = "Book"
    PENDING = "Pending"
    BOOKED = "Booked"
    REJECTED = "Rejected"

    STATUSES = (
        (BOOK, "Book"),
        (PENDING, "Pending"),
        (BOOKED, "Booked"),
        (REJECTED, "Rejected")
    )
    status = models.CharField(max_length=8, choices=STATUSES, default=PENDING)

    def __str__(self):
        return f"{self.venue} booked on {self.date} from {self.start} - {self.end}"


class ReservationRequest(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=11)
    email_address = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    pax = models.PositiveIntegerField()

    #Time info
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()

    def clean(self):
        if self.end <= self.start:
            raise ValidationError('The reservation must end after the start time.')
        
        conflict = ReservationModel.objects.filter(
            venue = self.venue,
            date = self.date,
            start__lt = self.end,   #Existing start time falls before new end time
            end__gt = self.start,   #Existing end time falls after new start time
            status = ReservationModel.BOOKED
        )
        if conflict.exists():
            raise ValidationError('Sorry, there is a conflicting reservation. Please choose a different time or venue.')
        
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.contact_number}) - {self.venue} for {self.pax} people"



    
