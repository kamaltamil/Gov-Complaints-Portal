from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Complaint, StaffComment

User = get_user_model()

ALLOWED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_ATTACHMENT_SIZE_BYTES = 5 * 1024 * 1024


def validate_attachment(file_obj):
    extension = Path(file_obj.name).suffix.lower()
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise ValidationError("Only JPG, JPEG, PNG, and PDF files are allowed.")
    if file_obj.size > MAX_ATTACHMENT_SIZE_BYTES:
        raise ValidationError("Each file must be 5MB or smaller.")


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned_files = []
        errors = []
        for file_obj in data:
            try:
                cleaned_files.append(super().clean(file_obj, initial))
            except ValidationError as error:
                errors.extend(error.error_list)
        if errors:
            raise ValidationError(errors)
        return cleaned_files


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["title", "description", "category", "urgency", "location"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Brief complaint title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "urgency": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Location"}),
        }


class MultipleAttachmentForm(forms.Form):
    attachments = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": ".jpg,.jpeg,.png,.pdf",
            }
        ),
    )

    def clean_attachments(self):
        files = self.cleaned_data.get("attachments", [])
        for file_obj in files:
            validate_attachment(file_obj)
        return files


class StaffComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["status", "assigned_to", "staff_remark"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "staff_remark": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.current_status = kwargs.pop("current_status", None)
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True)
        self.fields["assigned_to"].required = False

    def clean_assigned_to(self):
        assigned_to = self.cleaned_data.get("assigned_to")
        if assigned_to and not assigned_to.is_staff:
            raise ValidationError("Assigned user must be a staff account.")
        return assigned_to

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        current_status = self.current_status or self.instance.status
        allowed_transitions = {
            Complaint.Status.RECEIVED: {Complaint.Status.RECEIVED, Complaint.Status.IN_PROGRESS},
            Complaint.Status.IN_PROGRESS: {Complaint.Status.IN_PROGRESS, Complaint.Status.RESOLVED},
            Complaint.Status.RESOLVED: {Complaint.Status.RESOLVED},
        }
        if new_status not in allowed_transitions.get(current_status, {current_status}):
            raise ValidationError("Invalid status transition.")
        return new_status


class StaffCommentForm(forms.ModelForm):
    class Meta:
        model = StaffComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Add an internal comment (staff only)",
                }
            )
        }

    def clean_comment(self):
        comment = self.cleaned_data.get("comment", "").strip()
        if comment and len(comment) < 3:
            raise ValidationError("Comment must be at least 3 characters.")
        return comment
