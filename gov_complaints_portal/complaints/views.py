from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView

from .forms import (
    ComplaintForm,
    MultipleAttachmentForm,
    SignUpForm,
    StaffCommentForm,
    StaffComplaintUpdateForm,
)
from .models import Attachment, Complaint, StaffComment


def apply_complaint_filters(queryset, params):
    query = params.get("q", "").strip()
    category = params.get("category", "").strip()
    status = params.get("status", "").strip()
    urgency = params.get("urgency", "").strip()
    start_date = params.get("start_date", "").strip()
    end_date = params.get("end_date", "").strip()

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query)
            | Q(reference_id__icontains=query)
            | Q(location__icontains=query)
        )
    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)
    if urgency:
        queryset = queryset.filter(urgency=urgency)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__date__gte=start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            queryset = queryset.filter(created_at__date__lte=end_dt)
        except ValueError:
            pass
    return queryset


def store_attachments(complaint, files):
    for file_obj in files:
        Attachment.objects.create(
            complaint=complaint,
            file=file_obj,
            original_filename=file_obj.name,
        )


def send_submission_email(complaint):
    if not complaint.user.email:
        return
    send_mail(
        subject=f"Complaint Submitted: {complaint.reference_id}",
        message=(
            f"Dear {complaint.user.username},\n\n"
            f"Your complaint has been submitted successfully.\n"
            f"Reference ID: {complaint.reference_id}\n"
            f"Status: {complaint.get_status_display()}\n\n"
            "We will notify you when there is an update."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[complaint.user.email],
        fail_silently=True,
    )


def send_status_change_email(complaint, old_status, new_status):
    if not complaint.user.email:
        return
    send_mail(
        subject=f"Complaint Status Updated: {complaint.reference_id}",
        message=(
            f"Dear {complaint.user.username},\n\n"
            f"Your complaint {complaint.reference_id} status changed from "
            f"{old_status.replace('_', ' ').title()} to {new_status.replace('_', ' ').title()}.\n\n"
            "Thank you."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[complaint.user.email],
        fail_silently=True,
    )


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Staff access required.")
        return super().handle_no_permission()


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["recent_complaints"] = Complaint.objects.filter(user=self.request.user)[:5]
        else:
            context["recent_complaints"] = []
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        messages.success(self.request, "Account created successfully. Please log in.")
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["complaints"] = Complaint.objects.filter(user=self.request.user)
        return context


class ComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = "complaints/complaint_list.html"
    context_object_name = "complaints"
    paginate_by = 10

    def get_queryset(self):
        queryset = Complaint.objects.select_related("user", "assigned_to")
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        queryset = apply_complaint_filters(queryset, self.request.GET)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Complaint.Category.choices
        context["statuses"] = Complaint.Status.choices
        context["urgency_choices"] = Complaint.Urgency.choices
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "category": self.request.GET.get("category", ""),
            "status": self.request.GET.get("status", ""),
            "urgency": self.request.GET.get("urgency", ""),
            "start_date": self.request.GET.get("start_date", ""),
            "end_date": self.request.GET.get("end_date", ""),
        }
        return context


class ComplaintCreateView(LoginRequiredMixin, View):
    template_name = "complaints/complaint_create.html"

    def get(self, request):
        context = {
            "form": ComplaintForm(),
            "attachment_form": MultipleAttachmentForm(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = ComplaintForm(request.POST)
        attachment_form = MultipleAttachmentForm(request.POST, request.FILES)
        if form.is_valid() and attachment_form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            store_attachments(complaint, attachment_form.cleaned_data["attachments"])
            send_submission_email(complaint)
            messages.success(request, f"Complaint submitted successfully. Reference: {complaint.reference_id}")
            return redirect("complaints:complaint_detail", reference_id=complaint.reference_id)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "attachment_form": attachment_form,
            },
        )


class ComplaintDetailView(LoginRequiredMixin, TemplateView):
    template_name = "complaints/complaint_detail.html"

    def get_complaint(self):
        complaint = get_object_or_404(
            Complaint.objects.select_related("user", "assigned_to"),
            reference_id=self.kwargs["reference_id"],
        )
        if not complaint.can_be_viewed_by(self.request.user):
            raise PermissionDenied("You do not have permission to view this complaint.")
        return complaint

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaint = self.get_complaint()
        context["complaint"] = complaint
        context["attachments"] = complaint.attachments.all()
        context["can_edit"] = complaint.can_be_modified_by_user(self.request.user)
        context["can_delete"] = complaint.can_be_modified_by_user(self.request.user)
        if self.request.user.is_staff:
            context["staff_update_form"] = StaffComplaintUpdateForm(
                instance=complaint,
                current_status=complaint.status,
            )
            context["staff_comment_form"] = StaffCommentForm()
            context["staff_comments"] = complaint.staff_comments.select_related("staff_user")
        return context


class ComplaintUpdateView(LoginRequiredMixin, View):
    template_name = "complaints/complaint_edit.html"

    def get_complaint(self, request, reference_id):
        complaint = get_object_or_404(Complaint, reference_id=reference_id)
        if complaint.user_id != request.user.id:
            raise PermissionDenied("You can only edit your own complaints.")
        if complaint.status != Complaint.Status.RECEIVED:
            raise PermissionDenied("Only complaints in 'Received' status can be edited.")
        return complaint

    def get(self, request, reference_id):
        complaint = self.get_complaint(request, reference_id)
        context = {
            "complaint": complaint,
            "form": ComplaintForm(instance=complaint),
            "attachment_form": MultipleAttachmentForm(),
        }
        return render(request, self.template_name, context)

    def post(self, request, reference_id):
        complaint = self.get_complaint(request, reference_id)
        form = ComplaintForm(request.POST, instance=complaint)
        attachment_form = MultipleAttachmentForm(request.POST, request.FILES)

        if form.is_valid() and attachment_form.is_valid():
            form.save()
            store_attachments(complaint, attachment_form.cleaned_data["attachments"])
            messages.success(request, "Complaint updated successfully.")
            return redirect("complaints:complaint_detail", reference_id=complaint.reference_id)

        return render(
            request,
            self.template_name,
            {
                "complaint": complaint,
                "form": form,
                "attachment_form": attachment_form,
            },
        )


class ComplaintDeleteView(LoginRequiredMixin, View):
    template_name = "complaints/complaint_delete.html"

    def get_complaint(self, request, reference_id):
        complaint = get_object_or_404(Complaint, reference_id=reference_id)
        if complaint.user_id != request.user.id:
            raise PermissionDenied("You can only delete your own complaints.")
        if complaint.status != Complaint.Status.RECEIVED:
            raise PermissionDenied("Only complaints in 'Received' status can be deleted.")
        return complaint

    def get(self, request, reference_id):
        complaint = self.get_complaint(request, reference_id)
        return render(request, self.template_name, {"complaint": complaint})

    def post(self, request, reference_id):
        complaint = self.get_complaint(request, reference_id)
        for attachment in complaint.attachments.all():
            attachment.file.delete(save=False)
        complaint.delete()
        messages.success(request, "Complaint deleted successfully.")
        return redirect("complaints:complaint_list")


class StaffDashboardView(StaffRequiredMixin, ListView):
    model = Complaint
    template_name = "complaints/complaint_staff_dashboard.html"
    context_object_name = "complaints"
    paginate_by = 10

    def get_queryset(self):
        queryset = Complaint.objects.select_related("user", "assigned_to")
        queryset = apply_complaint_filters(queryset, self.request.GET)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Complaint.Category.choices
        context["statuses"] = Complaint.Status.choices
        context["urgency_choices"] = Complaint.Urgency.choices
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "category": self.request.GET.get("category", ""),
            "status": self.request.GET.get("status", ""),
            "urgency": self.request.GET.get("urgency", ""),
            "start_date": self.request.GET.get("start_date", ""),
            "end_date": self.request.GET.get("end_date", ""),
        }
        return context


class StaffComplaintUpdateView(StaffRequiredMixin, View):
    def post(self, request, reference_id):
        complaint = get_object_or_404(Complaint, reference_id=reference_id)
        previous_status = complaint.status

        update_form = StaffComplaintUpdateForm(
            request.POST,
            instance=complaint,
            current_status=complaint.status,
        )
        comment_form = StaffCommentForm(request.POST)

        if update_form.is_valid() and comment_form.is_valid():
            updated_complaint = update_form.save(commit=False)
            if updated_complaint.status != previous_status:
                updated_complaint.last_status_updated_at = timezone.now()
            updated_complaint.save()

            comment_text = comment_form.cleaned_data.get("comment", "").strip()
            if comment_text:
                StaffComment.objects.create(
                    complaint=updated_complaint,
                    staff_user=request.user,
                    comment=comment_text,
                )

            if updated_complaint.status != previous_status:
                send_status_change_email(
                    updated_complaint,
                    previous_status,
                    updated_complaint.status,
                )
            messages.success(request, "Complaint updated successfully.")
        else:
            errors = []
            errors.extend(update_form.errors.get("__all__", []))
            errors.extend(comment_form.errors.get("__all__", []))
            if not errors:
                for field, field_errors in update_form.errors.items():
                    errors.extend([f"{field}: {error}" for error in field_errors])
                for field, field_errors in comment_form.errors.items():
                    errors.extend([f"{field}: {error}" for error in field_errors])
            for error in errors:
                messages.error(request, error)

        return redirect("complaints:complaint_detail", reference_id=reference_id)

    def get(self, request, reference_id):
        return redirect("complaints:complaint_detail", reference_id=reference_id)


class AttachmentDownloadView(LoginRequiredMixin, View):
    def get(self, request, attachment_id):
        attachment = get_object_or_404(
            Attachment.objects.select_related("complaint", "complaint__user"),
            pk=attachment_id,
        )
        complaint = attachment.complaint
        if not complaint.can_be_viewed_by(request.user):
            raise PermissionDenied("You do not have permission to access this file.")
        if not attachment.file:
            raise Http404("File not found.")

        inline = request.GET.get("inline") == "1"
        filename = attachment.original_filename or attachment.file.name.rsplit("/", maxsplit=1)[-1]
        return FileResponse(
            attachment.file.open("rb"),
            as_attachment=not inline,
            filename=filename,
        )
