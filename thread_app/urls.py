# thread_app/urls.py

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect root URL "/" to the login page
    path("", RedirectView.as_view(pattern_name="login", permanent=False)),

    path("admin/", admin.site.urls),

    # Auth URLs
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Inventory app URLs (dashboard, register, issuance, logs, etc.)
    path("", include("inventory.urls")),
]
