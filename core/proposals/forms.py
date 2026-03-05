from django import forms
from .models import Proposal


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = [
            'title', 'nature_of_activity', 'target_attendees', 
            'objectives', 'start_datetime', 'end_datetime', 'reviewing_office'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input border rounded p-2 w-full'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input border rounded p-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'form-input border rounded p-2 w-full'}),
            'nature_of_activity': forms.TextInput(attrs={'class': 'form-input border rounded p-2 w-full'}),
            'target_attendees': forms.TextInput(attrs={'class': 'form-input border rounded p-2 w-full'}),
            'objectives': forms.Textarea(attrs={'class': 'form-textarea border rounded p-2 w-full', 'rows': 4}),
            'reviewing_office': forms.Select(attrs={'class': 'form-select border rounded p-2 w-full'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Check what the user clicked (draft or submit)
        action = self.data.get('action')

        # REQ-2 & REQ-10: If submitting, validate that all fields are filled
        if action == 'submit':
            required_fields = [
                'title', 'nature_of_activity', 'target_attendees', 
                'objectives', 'start_datetime', 'end_datetime', 'reviewing_office'
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required for final submission.')
                    
            # Date validation
            start = cleaned_data.get('start_datetime')
            end = cleaned_data.get('end_datetime')
            if start and end and start >= end:
                self.add_error('end_datetime', 'End time must be after start time.')

        # REQ-9: If draft, we bypass the required checks (they are allowed to be empty)
        return cleaned_data