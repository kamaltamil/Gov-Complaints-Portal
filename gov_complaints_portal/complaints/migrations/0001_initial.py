# Generated manually for initial project scaffold.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference_id", models.CharField(blank=True, max_length=24, null=True, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("sanitation", "Sanitation"),
                            ("infrastructure", "Infrastructure"),
                            ("utilities", "Utilities"),
                            ("public_safety", "Public Safety"),
                            ("healthcare", "Healthcare"),
                            ("education", "Education"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("received", "Received"),
                            ("in_progress", "In Progress"),
                            ("resolved", "Resolved"),
                        ],
                        default="received",
                        max_length=20,
                    ),
                ),
                (
                    "urgency",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        default="medium",
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_status_updated_at", models.DateTimeField(blank=True, null=True)),
                ("staff_remark", models.TextField(blank=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_complaints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="complaints",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Attachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="complaint_attachments/%Y/%m/%d/")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                (
                    "complaint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="complaints.complaint",
                    ),
                ),
            ],
            options={"ordering": ["uploaded_at"]},
        ),
        migrations.CreateModel(
            name="StaffComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("comment", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "complaint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="staff_comments",
                        to="complaints.complaint",
                    ),
                ),
                (
                    "staff_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="complaint_staff_comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
