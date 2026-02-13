from django.urls import path

from .views import (
    AttachmentDownloadView,
    ComplaintCreateView,
    ComplaintDeleteView,
    ComplaintDetailView,
    ComplaintListView,
    ComplaintUpdateView,
    StaffComplaintUpdateView,
    StaffDashboardView,
)

app_name = "complaints"

urlpatterns = [
    path("complaints/", ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/new/", ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaints/<str:reference_id>/", ComplaintDetailView.as_view(), name="complaint_detail"),
    path("complaints/<str:reference_id>/edit/", ComplaintUpdateView.as_view(), name="complaint_edit"),
    path("complaints/<str:reference_id>/delete/", ComplaintDeleteView.as_view(), name="complaint_delete"),
    path("staff/dashboard/", StaffDashboardView.as_view(), name="staff_dashboard"),
    path(
        "staff/complaints/<str:reference_id>/update-status/",
        StaffComplaintUpdateView.as_view(),
        name="staff_update_status",
    ),
    path("attachments/<int:attachment_id>/download/", AttachmentDownloadView.as_view(), name="attachment_download"),
]
