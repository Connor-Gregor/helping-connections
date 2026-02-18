from django import forms
from django.contrib.auth.models import User
from .models import Profile

ROLE_CHOICES = [
    ("unhoused", "Unhoused"),
    ("volunteer", "Volunteer"),
]

class RegisterForm(forms.Form):
    display_username = forms.CharField(
        max_length=30,
        help_text="Public username (ex: Firstname_Lastname)",
    )
    email = forms.EmailField()
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional",
    )
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    def clean_display_username(self):
        username = self.cleaned_data["display_username"].strip()

        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")

        # simple character policy (optional but helpful)
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        if any(ch not in allowed for ch in username):
            raise forms.ValidationError("Username can only use letters, numbers, _, -, and .")

        if Profile.objects.filter(display_username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        # You currently store email in User.username, so check that
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        # keep it simple for sprint: allow blank, otherwise basic length check
        if phone and len(phone) < 7:
            raise forms.ValidationError("Phone number looks too short.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        return cleaned

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)