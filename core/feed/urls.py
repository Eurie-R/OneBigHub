from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.feed_list, name='feed_list'),
    path('create/', views.feed_create, name='feed_create'),
    path('<int:pk>/', views.feed_detail, name='feed_detail'),
    path('<int:pk>/edit/', views.feed_edit, name='feed_edit'),
    path('<int:pk>/delete/', views.feed_delete, name='feed_delete'),
    
    path('api/', views.post_list, name='post_list'),
    path('api/create/', views.post_create, name='post_create'),
    path('api/<int:pk>/', views.post_detail, name='post_detail_api'),
]