from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'event_start', 'event_end', 'location']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-ateneo-blue'
            }),
            'body': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg p-2 h-32 focus:outline-none focus:ring-2 focus:ring-ateneo-blue'
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
                'class': 'w-full border border-gray-300 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-ateneo-blue'
            }),
        }
