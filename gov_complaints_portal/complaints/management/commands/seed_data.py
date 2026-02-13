from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from complaints.models import Complaint, StaffComment

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with sample users and complaints."

    def handle(self, *args, **options):
        staff_user, created_staff = User.objects.get_or_create(
            username="staff_admin",
            defaults={
                "email": "staff_admin@example.com",
                "is_staff": True,
                "is_superuser": False,
            },
        )
        if created_staff:
            staff_user.set_password("StaffPass123!")
            staff_user.save()

        citizen_user, created_citizen = User.objects.get_or_create(
            username="citizen_user",
            defaults={"email": "citizen_user@example.com"},
        )
        if created_citizen:
            citizen_user.set_password("CitizenPass123!")
            citizen_user.save()

        sample_definitions = [
            {
                "title": "Overflowing Garbage Bins",
                "description": "Municipal bins are not being cleared regularly in Zone 2.",
                "category": Complaint.Category.SANITATION,
                "urgency": Complaint.Urgency.HIGH,
                "location": "Zone 2 - Main Street",
                "status": Complaint.Status.RECEIVED,
            },
            {
                "title": "Potholes on City Road",
                "description": "Large potholes causing traffic congestion and accidents.",
                "category": Complaint.Category.INFRASTRUCTURE,
                "urgency": Complaint.Urgency.CRITICAL,
                "location": "Ring Road Block A",
                "status": Complaint.Status.IN_PROGRESS,
            },
            {
                "title": "Streetlights Not Working",
                "description": "Streetlights remain off at night near public park.",
                "category": Complaint.Category.UTILITIES,
                "urgency": Complaint.Urgency.MEDIUM,
                "location": "Public Park Road",
                "status": Complaint.Status.RESOLVED,
            },
        ]

        created_count = 0
        for item in sample_definitions:
            complaint, created = Complaint.objects.get_or_create(
                user=citizen_user,
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "category": item["category"],
                    "urgency": item["urgency"],
                    "location": item["location"],
                    "status": item["status"],
                    "assigned_to": staff_user if item["status"] != Complaint.Status.RECEIVED else None,
                    "last_status_updated_at": timezone.now()
                    if item["status"] != Complaint.Status.RECEIVED
                    else None,
                    "staff_remark": "Auto-seeded complaint for demo use.",
                },
            )
            if created:
                created_count += 1
                if complaint.status != Complaint.Status.RECEIVED:
                    StaffComment.objects.get_or_create(
                        complaint=complaint,
                        staff_user=staff_user,
                        comment="Complaint has been reviewed by staff.",
                    )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(
            self.style.WARNING(
                "Credentials: citizen_user / CitizenPass123!, "
                "staff_admin / StaffPass123!"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"New complaints created: {created_count}"))
