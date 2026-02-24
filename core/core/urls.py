"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Allauth - handles Google OAuth login/logout
    path('accounts/', include('allauth.urls')),

    # One Big Hub apps
    path('api/users/', include('users.urls')),     # Feature 4.1
    path('api/venues/', include('venues.urls')),         # Feature 4.2
    path('api/proposals/', include('proposals.urls')),   # Feature 4.3
    path('api/reviews/', include('reviews.urls', 'admin_reviews')),       # Feature 4.4
    path('api/feed/', include('feed.urls')),             # Feature 4.5

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
