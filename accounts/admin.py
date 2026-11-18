from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Club, ClubMembership, Division, User

admin.site.register(User, UserAdmin)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ["name", "division"]
    list_filter = ["division"]
    search_fields = ["name"]
    autocomplete_fields = ["division"]


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "club", "role", "is_active"]
    list_filter = ["role", "is_active", "club"]
    search_fields = ["user__username", "club__name"]
    autocomplete_fields = ["user", "club"]

# Register your models here.
