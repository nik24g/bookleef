from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuthorProfile, Book, InternalNote, Ticket, TicketMessage, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "role", "is_staff")
    list_filter = ("role",)
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)


admin.site.register(AuthorProfile)
admin.site.register(Book)
admin.site.register(Ticket)
admin.site.register(TicketMessage)
admin.site.register(InternalNote)
