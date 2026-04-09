from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'organization', 'title', 'event_start', 'event_end', 'created_at']
    list_filter = ['organization', 'created_at']
    search_fields = ['title', 'body', 'organization__org_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
