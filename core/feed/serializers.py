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
            'picture',
            'event_start',
            'event_end',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

class PostCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = [
            'title',
            'body',
            'picture',
            'event_start',
            'event_end',
            'location',
        ]

    def validate(self, attrs):
        start = attrs.get('event_start')
        end=attrs.get('event_end')
        if bool(start) != bool(end):
            raise serializers.ValidationError(
                "Both event_start and event_end must be provided together."
            )
        if start and end and end <= start:
            raise serializers.ValidationError(
                "event_end must be after event_start."
            )
        return attrs