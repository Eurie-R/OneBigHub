from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('create/', views.create_proposal, name='create_proposal'),
    path('<int:pk>/edit/', views.edit_proposal, name='edit_proposal'),
    path('<int:pk>/', views.proposal_detail, name='proposal_detail'),
]