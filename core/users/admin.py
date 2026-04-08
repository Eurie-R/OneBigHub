from django.contrib import admin
from .models import User, AdminOfficeProfile
# Register your models here.

@admin.register(User)
class UserModel(admin.ModelAdmin):
    list_display = ["email", "role", "USERNAME_FIELD", "REQUIRED_FIELDS"]

@admin.register(AdminOfficeProfile)
class AdminOfficeProfile(admin.ModelAdmin):
    list_display = ["user", "office_name", "office_type", "contact_email", "building", "room_number"]

