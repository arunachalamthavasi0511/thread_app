from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User

from io import BytesIO
import qrcode
from django.http import HttpResponse


from .models import Thread, Issuance, Profile
from .forms import ThreadForm, IssuanceForm, UserCreateForm
from .utils import is_admin, is_power, is_user
from django.contrib.auth import login
from django.contrib.auth.models import User

from django.db.models import Q
from django.http import HttpResponse
import csv

from django.urls import reverse
from django.db.models import Sum



@login_required
def dashboard(request):
    threads = Thread.objects.order_by("available_quantity")

    # Check if this user can approve
    can_approve = is_admin(request.user) or is_power(request.user)

    pending_count = 0
    if can_approve:
        pending_count = Issuance.objects.filter(status="PENDING").count()

    return render(request, "inventory/dashboard.html", {
        "threads": threads,
        "can_approve": can_approve,
        "pending_count": pending_count,
    })



@login_required
def register_thread(request):
    # Only Admin or Power user
    if not (is_admin(request.user) or is_power(request.user)):
        messages.error(request, "You do not have permission to register threads.")
        return redirect("dashboard")

    if request.method == "POST":
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.created_by = request.user
            thread.save()
            messages.success(request, "Thread registered successfully!")
            return redirect("dashboard")
    else:
        form = ThreadForm()

    return render(request, "inventory/register_thread.html", {"form": form})


@login_required
def issuance(request):
    # Column filter (from column detail page)
    column = request.GET.get("column") or request.POST.get("column")

    if request.method == "POST":
        form = IssuanceForm(request.POST, column=column)
        if form.is_valid():
            issuance = form.save(commit=False)
            issuance.requested_by = request.user
            issuance.bin_snapshot = issuance.thread.bin_no
            issuance.column_snapshot = issuance.thread.column_name

            # Admin / Power: auto-approve their own request
            if is_admin(request.user) or is_power(request.user):
                thread = issuance.thread
                if thread.available_quantity < issuance.requested_quantity:
                    messages.error(request, "Not enough stock!")
                    return redirect("issuance")

                thread.available_quantity -= issuance.requested_quantity
                thread.save()

                issuance.status = "APPROVED"
                issuance.approved_by = request.user
                issuance.approved_at = timezone.now()
                issuance.receipt_number = f"R{int(timezone.now().timestamp())}"
                issuance.save()

                messages.success(request, "Issuance approved and stock updated.")
                return redirect("receipt", issuance.id)
            else:
                issuance.status = "PENDING"
                issuance.save()
                messages.info(request, "Issuance request created and waiting for approval.")
                return redirect("dashboard")
    else:
        form = IssuanceForm(column=column)

    return render(request, "inventory/issuance.html", {
        "form": form,
        "column": column,
    })


@login_required
def approve_issuance(request, id):
    if not (is_admin(request.user) or is_power(request.user)):
        messages.error(request, "You do not have permission to approve issuances.")
        return redirect("dashboard")

    issuance = get_object_or_404(Issuance, id=id)
    thread = issuance.thread

    if thread.available_quantity < issuance.requested_quantity:
        messages.error(request, "Not enough stock to approve!")
        return redirect("dashboard")

    thread.available_quantity -= issuance.requested_quantity
    thread.save()

    issuance.status = "APPROVED"
    issuance.approved_by = request.user
    issuance.approved_at = timezone.now()
    issuance.receipt_number = f"R{int(timezone.now().timestamp())}"
    issuance.save()

    messages.success(request, "Issuance approved.")
    return redirect("receipt", issuance.id)


@login_required
def receipt(request, id):
    issuance = get_object_or_404(Issuance, id=id)
    return render(request, "inventory/receipt.html", {"i": issuance})

@login_required
def registration_logs(request):
    q = request.GET.get("q", "").strip()

    threads = Thread.objects.all()
    if q:
        threads = threads.filter(
            Q(shade__icontains=q)
            | Q(tkt__icontains=q)
            | Q(bin_no__icontains=q)
            | Q(column_name__icontains=q)
            | Q(brand__icontains=q)
        )

    threads = threads.order_by("-registration_date")

    return render(request, "inventory/registration_logs.html", {
        "threads": threads,
        "q": q,
    })


@login_required
def issuance_logs(request):
    q = request.GET.get("q", "").strip()

    issuances = Issuance.objects.select_related("thread", "requested_by", "approved_by")
    if q:
        issuances = issuances.filter(
            Q(thread__shade__icontains=q)
            | Q(thread__tkt__icontains=q)
            | Q(requested_by__username__icontains=q)
            | Q(approved_by__username__icontains=q)
            | Q(status__icontains=q)
        )

    issuances = issuances.order_by("-requested_at")

    return render(request, "inventory/issuance_logs.html", {
        "issuances": issuances,
        "q": q,
    })


@login_required
def registration_logs_export(request):
    q = request.GET.get("q", "").strip()

    threads = Thread.objects.all()
    if q:
        threads = threads.filter(
            Q(shade__icontains=q)
            | Q(tkt__icontains=q)
            | Q(bin_no__icontains=q)
            | Q(column_name__icontains=q)
            | Q(brand__icontains=q)
        )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="thread_registrations.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "Shade", "Tkt", "Bin No", "Column", "Category",
        "Brand", "Available Qty", "Registered At", "Created By",
    ])

    for t in threads:
        writer.writerow([
            t.shade,
            t.tkt,
            t.bin_no,
            t.column_name,
            t.get_category_display(),
            t.brand,
            t.available_quantity,
            t.registration_date.strftime("%Y-%m-%d %H:%M:%S"),
            t.created_by.username if t.created_by else "",
        ])

    return response


@login_required
def issuance_logs_export(request):
    q = request.GET.get("q", "").strip()

    issuances = Issuance.objects.select_related("thread", "requested_by", "approved_by")
    if q:
        issuances = issuances.filter(
            Q(thread__shade__icontains=q)
            | Q(thread__tkt__icontains=q)
            | Q(requested_by__username__icontains=q)
            | Q(approved_by__username__icontains=q)
            | Q(status__icontains=q)
        )

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="issuance_logs.csv"'
    writer = csv.writer(response)

    writer.writerow([
        "Thread", "Shade", "Tkt", "Qty", "Status",
        "Requested By", "Requested At", "Approved By", "Approved At",
        "Bin", "Column", "Receipt No",
    ])

    for i in issuances:
        writer.writerow([
            str(i.thread),
            i.thread.shade,
            i.thread.tkt,
            i.requested_quantity,
            i.status,
            i.requested_by.username if i.requested_by else "",
            i.requested_at.strftime("%Y-%m-%d %H:%M:%S"),
            i.approved_by.username if i.approved_by else "",
            i.approved_at.strftime("%Y-%m-%d %H:%M:%S") if i.approved_at else "",
            i.bin_snapshot,
            i.column_snapshot,
            i.receipt_number,
        ])

    return response


@login_required
def logs(request):
    # Simple redirect to registration logs
    return redirect("registration_logs")



@login_required
def user_management(request):
    # Only admin can manage users
    if not is_admin(request.user):
        messages.error(request, "Only admin can manage users.")
        return redirect("dashboard")

    # Ensure every existing user has a Profile
    from django.contrib.auth.models import User  # safe even if already imported

    for u in User.objects.all():
        Profile.objects.get_or_create(
            user=u,
            defaults={"role": "ADMIN" if u.is_superuser else "USER"}
        )

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
            else:
                user = User.objects.create_user(username=username, password=password)
                Profile.objects.create(user=user, role=role)
                messages.success(request, f"User '{username}' created with role {role}.")
                return redirect("user_management")
    else:
        form = UserCreateForm()

    # Build a safe list of user + role text (no direct u.profile usage in template)
    users_raw = User.objects.all().order_by("username")
    role_display_map = dict(Profile.ROLE_CHOICES)

    users = []
    for u in users_raw:
        profile = getattr(u, "profile", None)
        if profile is not None:
            role_code = profile.role
            role_display = role_display_map.get(role_code, role_code)
        else:
            role_code = "-"
            role_display = "-"

        users.append({
            "username": u.username,
            "is_superuser": u.is_superuser,
            "role_code": role_code,
            "role_display": role_display,
        })

    return render(request, "inventory/user_management.html", {
        "form": form,
        "users": users,
    })

@login_required
def pending_issuances(request):
    # Only Admin or Power User can see this page
    if not (is_admin(request.user) or is_power(request.user)):
        messages.error(request, "You do not have permission to view approvals.")
        return redirect("dashboard")

    pending = Issuance.objects.filter(status="PENDING").order_by("-requested_at")

    return render(request, "inventory/pending_issuances.html", {
        "pending": pending,
    })

def viewer_login(request):
    # Only allow POST for safety
    if request.method != "POST":
        return redirect("login")

    # Get or create a shared viewer user
    user, created = User.objects.get_or_create(username="viewer")
    if created:
        user.set_unusable_password()
        user.save()

    # Ensure profile exists with VIEWER role
    Profile.objects.get_or_create(user=user, defaults={"role": "VIEWER"})

    # Log in this viewer user
    login(request, user)

    return redirect("dashboard")

@login_required
def column_list(request):
    # Get distinct column names with total available quantity
    columns_qs = (
        Thread.objects
        .values("column_name")
        .annotate(total_qty=Sum("available_quantity"))
        .order_by("column_name")
    )

    columns = []
    for col in columns_qs:
        name = col["column_name"]
        url = request.build_absolute_uri(
            reverse("column_detail", args=[name])
        )
        columns.append({
            "name": name,
            "total_qty": col["total_qty"],
            "url": url,  # used for QR code
        })

    return render(request, "inventory/column_list.html", {
        "columns": columns,
    })


@login_required
def column_detail(request, column_name):
    threads = Thread.objects.filter(column_name=column_name).order_by("bin_no", "shade", "tkt")
    total_qty = threads.aggregate(total=Sum("available_quantity"))["total"] or 0

    return render(request, "inventory/column_detail.html", {
        "column_name": column_name,
        "threads": threads,
        "total_qty": total_qty,
    })

@login_required
def column_qr(request, column_name):
    # Build the full URL for this column's detail page
    url = request.build_absolute_uri(
        reverse("column_detail", args=[column_name])
    )

    # Generate QR code image in memory
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    return HttpResponse(image_bytes, content_type="image/png")
