from django.urls import path
from .views import RegisterView, LoginView, LogoutView, CurrentUserView, OrganizationProfileView, AdminOfficeProfileView, landing_page, login_page, register_page, profile_setup_page ,dashboard_page


app_name = 'users'

urlpatterns = [
    # Template URLs
    path('', landing_page, name='landing'),
    path('login/', login_page, name='login_page'),
    path('register/', register_page, name='register_page'),
    path('dashboard/', dashboard_page, name='dashboard'),

    # API URLs
    path('api/users/register/', RegisterView.as_view(), name='register'),
    path('api/users/login/', LoginView.as_view(), name='login'),
    path('api/users/logout/', LogoutView.as_view(), name='logout'),
    path('api/users/me/', CurrentUserView.as_view(), name='current-user'),
    path('api/users/profile/org/', OrganizationProfileView.as_view(), name='org-profile'),
    path('api/users/profile/admin/', AdminOfficeProfileView.as_view(), name='admin-profile'),
    path('profile/setup/', profile_setup_page, name='profile_setup'),
]


