from django.contrib import admin
from django.urls import include, path

from complaints.views import HomeView, ProfileView, SignUpView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", HomeView.as_view(), name="home"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("complaints.urls")),
]
