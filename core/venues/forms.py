from django import forms
from .models import ReservationRequest

class ReservationRequestForm(forms.ModelForm):
    class Meta:
        model = ReservationRequest
        exclude = ['venue', 'status']

        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'First name',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Last name',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'contact_number': forms.TextInput(attrs={
                'placeholder': 'Contact number (e.g. 09171234567)',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'email_address': forms.EmailInput(attrs={
                'placeholder': 'Must match your login email',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'purpose': forms.TextInput(attrs={
                'placeholder': 'Purpose of reservation',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'pax': forms.NumberInput(attrs={
                'placeholder': 'Number of attendees',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'start': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
            'end': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border border-gray-200 rounded-lg'
            }),
        }
