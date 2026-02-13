from django.contrib import admin

from .models import Attachment, Complaint, StaffComment


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("uploaded_at", "original_filename")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "reference_id",
        "title",
        "category",
        "status",
        "urgency",
        "user",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "category", "urgency", "created_at")
    search_fields = ("reference_id", "title", "user__username", "location")
    readonly_fields = ("reference_id", "created_at", "updated_at", "last_status_updated_at")
    inlines = [AttachmentInline]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "complaint", "original_filename", "uploaded_at")
    search_fields = ("complaint__reference_id", "original_filename")
    readonly_fields = ("uploaded_at",)


@admin.register(StaffComment)
class StaffCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "complaint", "staff_user", "created_at")
    search_fields = ("complaint__reference_id", "staff_user__username", "comment")
    readonly_fields = ("created_at",)
