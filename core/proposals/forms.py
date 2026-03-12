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
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')

        if start and end:
            if end <= start:
                self.add_error('end_datetime', "End time must be after start time.")
            
            # Check for overlapping proposals
            from .models import Proposal
            overlapping_proposals = Proposal.objects.filter(
                status__in=[Proposal.Status.SUBMITTED, Proposal.Status.APPROVED],
                start_datetime__lt=end,
                end_datetime__gt=start
            )

            # If editing a draft exclude the current proposal from the check
            if self.instance and self.instance.pk:
                overlapping_proposals = overlapping_proposals.exclude(pk=self.instance.pk)

            if overlapping_proposals.exists():
                self.add_error(None, "This time slot has already been booked by another proposal.")

        return cleaned_data