from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("POWER", "Power User"),
        ("USER", "User"),
        ("VIEWER", "Viewer"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="USER")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Thread(models.Model):
    CATEGORY_CHOICES = [
        ("DOMESTIC", "Domestic"),
        ("EXPORT", "Export"),
    ]

    registration_date = models.DateTimeField(auto_now_add=True)
    shade = models.CharField(max_length=100)
    tkt = models.CharField(max_length=100)
    bin_no = models.CharField(max_length=100)
    available_quantity = models.PositiveIntegerField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    brand = models.CharField(max_length=100)
    column_name = models.CharField(max_length=100)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.shade} - {self.tkt} - {self.bin_no}"


class Issuance(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    requested_quantity = models.PositiveIntegerField()

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="req_by")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="app_by")

    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    bin_snapshot = models.CharField(max_length=100)
    column_snapshot = models.CharField(max_length=100)

    receipt_number = models.CharField(max_length=50, blank=True)

    rejection_reason = models.CharField(max_length=50, blank=True)
    rejection_comment = models.TextField(blank=True)

    def __str__(self):
        return f"Issuance {self.id}"
