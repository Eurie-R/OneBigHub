from django import forms
from .models import ReservationRequest

class ReservationRequestForm(forms.ModelForm):
    class Meta:
        model = ReservationRequest
        exclude = ['venue']
