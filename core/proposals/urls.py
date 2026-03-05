from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('create/', views.create_proposal, name='create_proposal'),
]