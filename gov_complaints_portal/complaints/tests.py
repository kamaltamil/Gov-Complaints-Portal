import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Attachment, Complaint, StaffComment

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ComplaintPortalTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

        self.user = User.objects.create_user(
            username="citizen",
            email="citizen@example.com",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="othercitizen",
            email="other@example.com",
            password="StrongPass123!",
        )
        self.staff = User.objects.create_user(
            username="staffmod",
            email="staff@example.com",
            password="StrongPass123!",
            is_staff=True,
        )

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def create_complaint(self, user=None, **kwargs):
        user = user or self.user
        data = {
            "title": "Street light issue",
            "description": "Street light has been non-functional for 3 days.",
            "category": Complaint.Category.INFRASTRUCTURE,
            "urgency": Complaint.Urgency.MEDIUM,
            "location": "Ward 7",
            "user": user,
        }
        data.update(kwargs)
        return Complaint.objects.create(**data)

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user(self):
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_complaint_create_generates_reference_and_sends_email(self):
        self.client.login(username="citizen", password="StrongPass123!")
        upload = SimpleUploadedFile("report.pdf", b"%PDF-1.4 test file", content_type="application/pdf")

        response = self.client.post(
            reverse("complaints:complaint_create"),
            data={
                "title": "Water leakage",
                "description": "Main pipeline leaking in sector 4.",
                "category": Complaint.Category.UTILITIES,
                "urgency": Complaint.Urgency.HIGH,
                "location": "Sector 4",
                "attachments": [upload],
            },
        )

        self.assertEqual(response.status_code, 302)
        complaint = Complaint.objects.get(title="Water leakage")
        self.assertTrue(complaint.reference_id.startswith("GOV-CMP-"))
        self.assertEqual(len(mail.outbox), 1)

    def test_user_cannot_view_other_users_complaint(self):
        complaint = self.create_complaint(user=self.other_user)
        self.client.login(username="citizen", password="StrongPass123!")
        response = self.client.get(
            reverse("complaints:complaint_detail", kwargs={"reference_id": complaint.reference_id})
        )
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_edit_when_status_not_received(self):
        complaint = self.create_complaint(status=Complaint.Status.IN_PROGRESS)
        self.client.login(username="citizen", password="StrongPass123!")
        response = self.client.get(reverse("complaints:complaint_edit", kwargs={"reference_id": complaint.reference_id}))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_update_status_and_add_comment(self):
        complaint = self.create_complaint()
        self.client.login(username="staffmod", password="StrongPass123!")
        response = self.client.post(
            reverse("complaints:staff_update_status", kwargs={"reference_id": complaint.reference_id}),
            data={
                "status": Complaint.Status.IN_PROGRESS,
                "assigned_to": self.staff.id,
                "staff_remark": "Assigned to municipal maintenance team.",
                "comment": "Initial verification completed.",
            },
        )
        self.assertEqual(response.status_code, 302)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.Status.IN_PROGRESS)
        self.assertIsNotNone(complaint.last_status_updated_at)
        self.assertEqual(complaint.assigned_to, self.staff)
        self.assertTrue(StaffComment.objects.filter(complaint=complaint).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_non_staff_denied_staff_dashboard(self):
        self.client.login(username="citizen", password="StrongPass123!")
        response = self.client.get(reverse("complaints:staff_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_search_filter_and_pagination(self):
        self.client.login(username="citizen", password="StrongPass123!")
        for index in range(12):
            self.create_complaint(
                title=f"Complaint {index}",
                category=Complaint.Category.SANITATION,
                urgency=Complaint.Urgency.HIGH if index % 2 == 0 else Complaint.Urgency.LOW,
            )
        response = self.client.get(
            reverse("complaints:complaint_list"),
            data={"category": Complaint.Category.SANITATION},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["paginator"].per_page, 10)
        for complaint in response.context["complaints"]:
            self.assertEqual(complaint.category, Complaint.Category.SANITATION)

    def test_invalid_attachment_extension_rejected(self):
        self.client.login(username="citizen", password="StrongPass123!")
        invalid_upload = SimpleUploadedFile("malware.exe", b"test", content_type="application/octet-stream")
        response = self.client.post(
            reverse("complaints:complaint_create"),
            data={
                "title": "Invalid file test",
                "description": "Trying to upload invalid file.",
                "category": Complaint.Category.OTHER,
                "urgency": Complaint.Urgency.LOW,
                "location": "Test location",
                "attachments": [invalid_upload],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only JPG, JPEG, PNG, and PDF files are allowed.")
        self.assertFalse(Complaint.objects.filter(title="Invalid file test").exists())

    def test_attachment_secure_download_permissions(self):
        complaint = self.create_complaint(user=self.user)
        file_obj = SimpleUploadedFile("proof.pdf", b"%PDF test", content_type="application/pdf")
        attachment = Attachment.objects.create(complaint=complaint, file=file_obj, original_filename="proof.pdf")

        self.client.login(username="citizen", password="StrongPass123!")
        owner_response = self.client.get(reverse("complaints:attachment_download", kwargs={"attachment_id": attachment.id}))
        self.assertEqual(owner_response.status_code, 200)

        self.client.logout()
        self.client.login(username="othercitizen", password="StrongPass123!")
        unauthorized_response = self.client.get(
            reverse("complaints:attachment_download", kwargs={"attachment_id": attachment.id})
        )
        self.assertEqual(unauthorized_response.status_code, 403)
