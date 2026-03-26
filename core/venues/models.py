from django.db import models

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
    
class Reservation(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    reserver = models.CharField(max_length=255)

    #Time info
    date = models.DateField()
    res_start = models.TimeField()
    res_end = models.TimeField() ##Raise error if end is before start


    



    
