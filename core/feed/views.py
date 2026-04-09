from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
 
from users.permissions import IsAteneoUser, IsOrganization
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer

@api_view(['GET'])
@permission_classes([IsAteneoUser])
def post_list(request):

    posts = Post.objects.select_related('organization').all()
 
    org_id = request.query_params.get('org')
    if org_id:
        posts = posts.filter(organization__id=org_id)
 
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
