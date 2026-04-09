from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
 
from users.permissions import IsAteneoUser, IsOrganization
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer
from .forms import PostForm

@login_required
def feed_list(request):
    posts = Post.objects.select_related('organization').all()
    return render(request, 'feed/feed_list.html', {'posts': posts})

@login_required
def feed_detail(request, pk):
    post = get_object_or_404(Post.objects.select_related('organization'), pk=pk)
    return render(request, 'feed/feed_detail.html', {'post': post})

@login_required
def feed_create(request):
    if not request.user.is_org:
        messages.error(request, "Only organization accounts can create posts.")
        return redirect('feed:feed_list')
 
    try:
        org_profile = request.user.org_profile
    except Exception:
        messages.error(request, "Your account is not linked to an organization profile.")
        return redirect('feed:feed_list')
 
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.organization = org_profile
            post.save()
            messages.success(request, "Post published successfully.")
            return redirect('feed:feed_detail', pk=post.pk)
    else:
        form = PostForm()
 
    return render(request, 'feed/feed_form.html', {'form': form, 'edit_mode': False})

@login_required
def feed_edit(request, pk):
    post = get_object_or_404(Post.objects.select_related('organization'), pk=pk)
 
    if not request.user.is_org:
        messages.error(request, "Only organization accounts can edit posts.")
        return redirect('feed:feed_detail', pk=pk)
 
    try:
        org_profile = request.user.org_profile
    except Exception:
        messages.error(request, "Your account is not linked to an organization profile.")
        return redirect('feed:feed_list')
 
    if post.organization != org_profile:
        messages.error(request, "You can only edit your own organization's posts.")
        return redirect('feed:feed_detail', pk=pk)
 
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully.")
            return redirect('feed:feed_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
 
    return render(request, 'feed/feed_form.html', {'form': form, 'edit_mode': True})

@login_required
@require_POST
def feed_delete(request, pk):
    post = get_object_or_404(Post.objects.select_related('organization'), pk=pk)
 
    if not request.user.is_org:
        messages.error(request, "Only organization accounts can delete posts.")
        return redirect('feed:feed_detail', pk=pk)
 
    try:
        org_profile = request.user.org_profile
    except Exception:
        messages.error(request, "Your account is not linked to an organization profile.")
        return redirect('feed:feed_list')
 
    if post.organization != org_profile:
        messages.error(request, "You can only delete your own organization's posts.")
        return redirect('feed:feed_detail', pk=pk)
 
    post.delete()
    messages.success(request, "Post deleted.")
    return redirect('feed:feed_list')

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

    try:
        org_profile = request.user.org_profile
    except Exception:
        return Response(
            {"detail": "Your account is not linked to an organization profile."},
            status=status.HTTP_403_FORBIDDEN
        )

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
    try:
        org_profile = request.user.org_profile
    except Exception:
        return Response(
            {"detail": "Your account is not linked to an organization profile."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if post.organization != org_profile:
        return Response(
            {"detail": "You can only modify your own organization's posts."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'PUT':
        serializer = PostCreateSerializer(
            post,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            post = serializer.save()
            return Response(
                PostSerializer(post, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        post.delete()
        return Response(
            {"detail": "Post deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )