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

@api_view(['POST'])
@permission_classes([IsOrganization])
def post_create(request):

    serializer = PostCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        post = serializer.save(organization=org_profile)
        # Return the full representation (with embedded org info) after creation
        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAteneoUser])
def post_detail(request, pk):

    post = get_object_or_404(Post.objects.select_related('organization'), pk=pk)
 
    if request.method == 'GET':
        serializer = PostSerializer(post, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
 
    if not request.user.is_org:
        return Response(
            {"detail": "Only organization accounts can modify posts."},
            status=status.HTTP_403_FORBIDDEN
        )