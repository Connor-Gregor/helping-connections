from django.contrib import admin
from .models import Role, Profile, PoliceInteractionReport

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    search_fields = ("user__username", "user__email")
    list_filter = ("role",)

@admin.register(PoliceInteractionReport)
class PoliceInteractionReportAdmin(admin.ModelAdmin):
    list_display = ("location", "created_at")
    search_fields = ("location", "description")
