from django import forms
from django.utils import timezone
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'picture', 'event_start', 'event_end', 'location']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-ateneo-blue',
                'placeholder': 'Event name'
            }),

            'body': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 h-32 focus:outline-none focus:ring-2 focus:ring-ateneo-blue',
                'placeholder': 'Write event details, instructions, or important notes...'
            }),
            
            'picture': forms.FileInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg p-2',
            'accept': 'image/*'
            }),

            'event_start': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full border border-gray-300 rounded-lg p-2'
            }),

            'event_end': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full border border-gray-300 rounded-lg p-2'
            }),

            'location': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-ateneo-blue',
                'placeholder': 'e.g. MVP Roofdeck / Online via Zoom'
            }),
        }

    # VALIDATION
    def clean(self):
        cleaned_data = super().clean()

        event_start = cleaned_data.get('event_start')
        event_end = cleaned_data.get('event_end')

        # Normalize timezone and store back into cleaned_data
        if event_start and timezone.is_naive(event_start):
            event_start = timezone.make_aware(event_start)
            cleaned_data['event_start'] = event_start

        if event_end and timezone.is_naive(event_end):
            event_end = timezone.make_aware(event_end)
            cleaned_data['event_end'] = event_end

        now = timezone.now()

        # Prevent past event start
        if event_start and event_start < now:
            self.add_error(
                'event_start',
                'Event start cannot be in the past.'
            )

        # Ensure end is after start
        if event_start and event_end:
            if event_end <= event_start:
                self.add_error(
                    'event_end',
                    'Event end must be after event start.'
                )

        return cleaned_data
