from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('', views.proposal_list, name='proposal_list'),
    path('create/', views.create_proposal, name='create_proposal'),
    path('api/my-status/', views.proposal_status_api, name='proposal_status_api'),
    path('<int:pk>/', views.proposal_detail, name='proposal_detail'),
    path('<int:pk>/edit/', views.edit_proposal, name='edit_proposal'),
    path('<int:pk>/review/', views.review_proposal, name='review_proposal'),
]
