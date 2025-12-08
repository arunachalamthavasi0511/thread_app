from django import forms
from django.contrib.auth.models import User

from .models import Thread, Issuance, Profile

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ["shade", "tkt", "bin_no", "available_quantity", "category", "brand", "column_name"]
        widgets = {
            "shade": forms.TextInput(attrs={"class": "form-control", "list": "shade-list"}),
            "tkt": forms.TextInput(attrs={"class": "form-control", "list": "tkt-list"}),
            "bin_no": forms.TextInput(attrs={"class": "form-control", "list": "bin-list"}),
            "available_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "brand": forms.TextInput(attrs={"class": "form-control", "list": "brand-list"}),
            "column_name": forms.TextInput(attrs={"class": "form-control", "list": "column-list"}),
        }


class IssuanceForm(forms.ModelForm):
    class Meta:
        model = Issuance
        fields = ["thread", "requested_quantity"]
        widgets = {
            "thread": forms.Select(attrs={"class": "form-select"}),
            "requested_quantity": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        column = kwargs.pop("column", None)
        super().__init__(*args, **kwargs)
        if column:
            self.fields["thread"].queryset = Thread.objects.filter(column_name=column)
        else:
            self.fields["thread"].queryset = Thread.objects.all()



class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }


class RejectIssuanceForm(forms.Form):
    REASON_CHOICES = [
        ("FALSE_REQUEST", "Request raised incorrectly"),
        ("NOT_ENOUGH_STOCK", "Stock is not sufficient"),
        ("OTHER", "Other (enter comment)"),
    ]
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.RadioSelect
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=False,
    )

