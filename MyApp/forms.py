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


class ProfileSettingsForm(forms.Form):
    display_username = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    address_line1 = forms.CharField(required=False)
    address_line2 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state = forms.CharField(required=False)
    zip_code = forms.CharField(required=False)

    def __init__(self, *args, profile: Profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def clean_display_username(self):
        u = self.cleaned_data["display_username"].strip()

        if len(u) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")

        # Unique check (case-insensitive)
        qs = Profile.objects.filter(display_username__iexact=u).exclude(pk=self.profile.pk)
        if qs.exists():
            raise forms.ValidationError("That username is already taken.")

        return u


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, required=True)
    new_password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    new_password2 = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        pw = self.cleaned_data["current_password"]
        if not self.user.check_password(pw):
            raise forms.ValidationError("Current password is incorrect.")
        return pw

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Passwords do not match.")

        return cleaned


class DeleteAccountForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I understand this will permanently delete my account."
    )
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        pw = self.cleaned_data["password"]
        if not self.user.check_password(pw):
            raise forms.ValidationError("Password is incorrect.")
        return pw


class EmailChangeForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        def clean_email(self):
            email = self.cleaned_data["email"].strip().lower()
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise forms.ValidationError("That email is already in use.")
            return email


class RoleChangeForm(forms.Form):
    role = forms.ChoiceField(choices=[])

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_roles = allowed_roles or []
        self.fields["role"].choices = [(r, r.title()) for r in allowed_roles]

    def clean_role(self):
        r = self.cleaned_data["role"]
        if r not in self.allowed_roles:
            raise forms.ValidationError("Invalid role selection.")
        return r
