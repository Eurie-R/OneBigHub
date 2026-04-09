from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'picture', 'event_start', 'event_end', 'location']
        widgets = {
            'event_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'event_end':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
 
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('event_start')
        end = cleaned_data.get('event_end')
 
        if bool(start) != bool(end):
            raise forms.ValidationError(
                "Both event start and event end must be provided together."
            )
        if start and end and end <= start:
            raise forms.ValidationError(
                "Event end must be after event start."
            )
        return cleaned_data