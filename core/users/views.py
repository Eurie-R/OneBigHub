
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    OrganizationProfileSerializer, AdminOfficeProfileSerializer
)
from .models import OrganizationProfile, AdminOfficeProfile
from .permissions import IsProfileOwner


# ─────────────────────────────────────────────
# Template Views (renders HTML pages)
# ─────────────────────────────────────────────

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'landing.html')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'users/login.html')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    return render(request, 'users/register.html')


def dashboard_page(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    context = {'user': request.user}

    if request.user.is_org:
        try:
            context['profile'] = request.user.org_profile
        except OrganizationProfile.DoesNotExist:
            context['profile'] = None

    elif request.user.is_admin_office:
        try:
            context['profile'] = request.user.admin_profile
        except AdminOfficeProfile.DoesNotExist:
            context['profile'] = None

    return render(request, 'dashboard.html', context)


# ─────────────────────────────────────────────
# API Views (returns JSON)
# ─────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Registration successful.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return Response({
                    "message": "Login successful.",
                    "user": UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class OrganizationProfileView(APIView):
    permission_classes = [IsAuthenticated, IsProfileOwner]

    def get(self, request):
        try:
            profile = request.user.org_profile
            serializer = OrganizationProfileSerializer(profile)
            return Response(serializer.data)
        except OrganizationProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        try:
            profile = request.user.org_profile
            serializer = OrganizationProfileSerializer(
                profile, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except OrganizationProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminOfficeProfileView(APIView):
    permission_classes = [IsAuthenticated, IsProfileOwner]

    def get(self, request):
        try:
            profile = request.user.admin_profile
            serializer = AdminOfficeProfileSerializer(profile)
            return Response(serializer.data)
        except AdminOfficeProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        try:
            profile = request.user.admin_profile
            serializer = AdminOfficeProfileSerializer(
                profile, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AdminOfficeProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

def profile_setup_page(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    context = {'user': request.user}

    if request.user.is_org:
        context['profile'] = request.user.org_profile
    elif request.user.is_admin_office:
        context['profile'] = request.user.admin_profile

    return render(request, 'users/profile_setup.html', context)