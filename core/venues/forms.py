from django import forms
from .models import ReservationRequest

class ReservationForm(forms.ModelForm):
    class Meta:
        model = ReservationRequest
        fields = '__all__'
