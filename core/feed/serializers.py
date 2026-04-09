from rest_framework import serializers
from .models import Post
from users.models import OrganizationProfile

class PostOrgSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationProfile
        fields = ['id', 'org_name', 'logo']

class PostSerializer(serializers.ModelSerializer):
    organization = PostOrgSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'organization',
            'title',
            'body',
            'image',
            'event_start',
            'event_end',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

