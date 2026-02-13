import os

from django.conf import settings
from django.db import models


class Complaint(models.Model):
    class Category(models.TextChoices):
        SANITATION = "sanitation", "Sanitation"
        INFRASTRUCTURE = "infrastructure", "Infrastructure"
        UTILITIES = "utilities", "Utilities"
        PUBLIC_SAFETY = "public_safety", "Public Safety"
        HEALTHCARE = "healthcare", "Healthcare"
        EDUCATION = "education", "Education"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    reference_id = models.CharField(max_length=24, unique=True, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=Category.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    urgency = models.CharField(
        max_length=20,
        choices=Urgency.choices,
        default=Urgency.MEDIUM,
    )
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_complaints",
        null=True,
        blank=True,
    )
    last_status_updated_at = models.DateTimeField(null=True, blank=True)
    staff_remark = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_id or f"Complaint #{self.pk}"

    def generate_reference_id(self) -> str:
        complaint_year = self.created_at.year if self.created_at else self.pk
        return f"GOV-CMP-{complaint_year}-{self.pk:06d}"

    def can_be_modified_by_user(self, user) -> bool:
        return self.user_id == user.id and self.status == self.Status.RECEIVED

    def can_be_viewed_by(self, user) -> bool:
        return user.is_staff or self.user_id == user.id

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating and not self.reference_id:
            reference = self.generate_reference_id()
            Complaint.objects.filter(pk=self.pk).update(reference_id=reference)
            self.reference_id = reference


class Attachment(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="complaint_attachments/%Y/%m/%d/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.original_filename or os.path.basename(self.file.name)

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


class StaffComment(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="staff_comments",
    )
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaint_staff_comments",
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.staff_user.username} - {self.complaint.reference_id}"
