from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.register_thread, name="register_thread"),
    path("issuance/", views.issuance, name="issuance"),

    # Approvals + receipt
    path("approve/<int:id>/", views.approve_issuance, name="approve"),
    path("reject/<int:id>/", views.reject_issuance, name="reject_issuance"),
    path("receipt/<int:id>/", views.receipt, name="receipt"),

    # Logs - registration
    path("logs/registration/", views.registration_logs, name="registration_logs"),
    path("logs/registration/export/", views.registration_logs_export, name="registration_logs_export"),
    path("logs/registration/revert/<int:log_id>/", views.revert_registration, name="revert_registration"),

    # Logs - issuance
    path("logs/issuance/", views.issuance_logs, name="issuance_logs"),
    path("logs/issuance/export/", views.issuance_logs_export, name="issuance_logs_export"),

    # Columns
    path("columns/", views.column_list, name="column_list"),
    path("columns/<str:column_name>/", views.column_detail, name="column_detail"),
    path("columns/<str:column_name>/qr/", views.column_qr, name="column_qr"),

    # Users & approvals & viewer
    path("users/", views.user_management, name="user_management"),
    path("approvals/", views.pending_issuances, name="pending_issuances"),
    path("viewer-login/", views.viewer_login, name="viewer_login"),
]
