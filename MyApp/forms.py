from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Request, Offer, Role
import re
import requests

# This file contains all Django forms used in Helping Connections.
# Includes:
# - Authentication forms (login, register, password reset)
# - Profile/settings forms
# - Request and Offer model forms
# - Shared validation logic (ZIP, names, etc.)
#
# NOTE:
# Many validations here mirror frontend validation (auth.js),
# but backend validation is required for security and data integrity.

ROLE_CHOICES = [
    ("unhoused", "Unhoused"),
    ("volunteer", "Volunteer"),
]

STATE_CHOICES = [
    ("", "Select a state"),
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]

VALID_STATE_VALUES = {abbr for abbr, _ in STATE_CHOICES if abbr}

# Validates whether a ZIP code exists using an external API (Zippopotam.us)
# This prevents users from entering fake or invalid ZIP codes.
# Returns True if valid, False otherwise.
#
# NOTE:
# Uses the `requests` library → must be included in requirements.txt


def zip_code_exists(zip_code):
    normalized_zip = zip_code.strip()[:5]

    try:
        response = requests.get(
            f"https://api.zippopotam.us/us/{normalized_zip}",
            timeout=3
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

# Custom password reset form:
# Overrides default Django behavior to show an error if email does not exist.
# Default Django silently "succeeds" even if email is not found.


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        user_exists = User.objects.filter(email__iexact=email).exists()

        if not user_exists:
            raise forms.ValidationError("No account was found with that email address.")

        return email

# Handles user registration form.
# Includes full validation for:
# - username uniqueness (case-insensitive)
# - email uniqueness
# - names (only valid characters)
# - phone number normalization
# - address formatting
# - ZIP code validation via API
# - password validation (Django validators)
#
# NOTE:
# Many of these validations are duplicated in auth.js for live feedback,
# but backend validation is the main security.


class RegisterForm(forms.Form):
    display_username = forms.CharField(
        max_length=30,
    )
    email = forms.EmailField()

    first_name = forms.CharField(
        max_length=30,
        required=True,
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "(XXX) XXX-XXXX",
            "inputmode": "tel",
            "autocomplete": "tel",
        })
    )

    address_line1 = forms.CharField(
        max_length=255,
        required=True,
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
    )
    city = forms.CharField(
        max_length=100,
        required=True,
    )
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=True,
    )
    zip_code = forms.CharField(
        max_length=20,
        required=True,
    )

    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    def clean_display_username(self):
        username = self.cleaned_data["display_username"].strip()

        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        if any(ch not in allowed for ch in username):
            raise forms.ValidationError("Username can only use letters, numbers, _, -, and .")

        if Profile.objects.filter(display_username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"].strip()

        if len(first_name) < 2:
            raise forms.ValidationError("First name must be at least 2 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", first_name):
            raise forms.ValidationError(
                "First name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"].strip()

        if len(last_name) < 2:
            raise forms.ValidationError("Last name must be at least 2 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        if not phone:
            return phone

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")

        return digits

    def clean_address_line1(self):
        address = self.cleaned_data["address_line1"].strip()

        if len(address) < 5:
            raise forms.ValidationError("Enter a valid street address.")

        if not re.search(r"[A-Za-z0-9]", address):
            raise forms.ValidationError("Enter a valid street address.")

        return re.sub(r"\s{2,}", " ", address)

    def clean_address_line2(self):
        address2 = self.cleaned_data.get("address_line2", "").strip()
        return re.sub(r"\s{2,}", " ", address2)

    def clean_city(self):
        city = self.cleaned_data["city"].strip()

        if len(city) < 2:
            raise forms.ValidationError("Enter a valid city.")

        if not re.fullmatch(r"[A-Za-z .'-]+", city):
            raise forms.ValidationError(
                "City can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return city

    def clean_state(self):
        state = self.cleaned_data["state"]

        if not state:
            raise forms.ValidationError("Please select a state.")

        if state not in VALID_STATE_VALUES:
            raise forms.ValidationError("Please select a valid state.")

        return state

    def clean_zip_code(self):
        zip_code = self.cleaned_data["zip_code"].strip()

        if not re.fullmatch(r"\d{5}(-\d{4})?", zip_code):
            raise forms.ValidationError("Please enter a valid ZIP code format, like 53158.")

        if not zip_code_exists(zip_code):
            raise forms.ValidationError("That ZIP code was not found. Please enter a U.S. ZIP code.")

        return zip_code

    def clean_password1(self):
        password = self.cleaned_data["password1"]
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        role = cleaned.get("role")

        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")

        if not role:
            self.add_error("role", "Please select a role.")

        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

# Form used in Settings page for updating user profile.
# Similar validation to RegisterForm, but fields are optional.
# Excludes current user's own username when checking uniqueness.


class ProfileSettingsForm(forms.Form):
    display_username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={"id": "settings-display-username"})
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-first-name", "maxlength": "30"})
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-last-name", "maxlength": "30"})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            "id": "settings-phone",
            "placeholder": "(XXX) XXX-XXXX",
            "inputmode": "tel",
            "autocomplete": "tel",
        })
    )
    address_line1 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-address-line1"})
    )
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-address-line2"})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-city"})
    )
    state = forms.ChoiceField(
        choices=STATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"id": "settings-state"})
    )
    zip_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"id": "settings-zip"})
    )
    profile_photo = forms.ImageField(required=False)

    def __init__(self, *args, profile: Profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def clean_display_username(self):
        username = self.cleaned_data["display_username"].strip()

        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        if any(ch not in allowed for ch in username):
            raise forms.ValidationError("Username can only use letters, numbers, _, -, and .")

        qs = Profile.objects.filter(display_username__iexact=username).exclude(pk=self.profile.pk)
        if qs.exists():
            raise forms.ValidationError("That username is already taken.")

        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()

        if not first_name:
            return first_name

        if len(first_name) < 2:
            raise forms.ValidationError("First name must be at least 2 characters.")

        if len(first_name) > 30:
            raise forms.ValidationError("First name cannot exceed 30 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", first_name):
            raise forms.ValidationError(
                "First name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()

        if not last_name:
            return last_name

        if len(last_name) < 2:
            raise forms.ValidationError("Last name must be at least 2 characters.")

        if len(last_name) > 30:
            raise forms.ValidationError("Last name cannot exceed 30 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()

        if not phone:
            return phone

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")

        return digits

    def clean_address_line1(self):
        address = self.cleaned_data.get("address_line1", "").strip()

        if address and len(address) < 5:
            raise forms.ValidationError("Enter a valid street address.")

        if not re.search(r"[A-Za-z0-9]", address):
            raise forms.ValidationError("Enter a valid street address.")

        return re.sub(r"\s{2,}", " ", address)

    def clean_address_line2(self):
        address2 = self.cleaned_data.get("address_line2", "").strip()
        return re.sub(r"\s{2,}", " ", address2)

    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()

        if not city:
            return city

        if len(city) < 2:
            raise forms.ValidationError("Enter a valid city.")

        if not re.fullmatch(r"[A-Za-z .'-]+", city):
            raise forms.ValidationError(
                "can only contain letters, spaces, apostrophes, hyphens, and periods."
            )
        return city

    def clean_state(self):
        state = self.cleaned_data.get("state", "").strip()

        if state and len(state) < 2:
            raise forms.ValidationError("Enter a valid state.")

        if state not in VALID_STATE_VALUES:
            raise forms.ValidationError("Please select a valid state.")

        return state

    def clean_zip_code(self):
        zip_code = self.cleaned_data.get("zip_code", "").strip()

        if not zip_code:
            return zip_code

        if not re.fullmatch(r"\d{5}(-\d{4})?", zip_code):
            raise forms.ValidationError("Please enter a valid ZIP code format, like 53158.")

        if not zip_code_exists(zip_code):
            raise forms.ValidationError("That ZIP code was not found. Please enter a real U.S. ZIP code.")

        return zip_code

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")

        if not photo:
            return photo

        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Profile photo must be smaller than 5MB.")

        valid_types = ["image/jpeg", "image/png", "image/webp"]
        if hasattr(photo, "content_type") and photo.content_type not in valid_types:
            raise forms.ValidationError("Upload a JPG, PNG, or WEBP image.")

        return photo

# Handles password change inside settings page.
# Validates:
# - current password matches user
# - new password passes Django validators
# - confirmation matches


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "id": "settings-current-password",
            "autocomplete": "current-password"
        }),
        required=True
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "id": "settings-new-password1",
            "autocomplete": "new-password"
        }),
        required=True
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "id": "settings-new-password2",
            "autocomplete": "new-password"
        }),
        required=True
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        pw = self.cleaned_data["current_password"]
        if not self.user.check_password(pw):
            raise forms.ValidationError("Current password is incorrect.")
        return pw

    def clean_new_password1(self):
        pw = self.cleaned_data["new_password1"]
        validate_password(pw, self.user)
        return pw

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Passwords do not match.")

        return cleaned

# Requires user to confirm deletion AND re-enter password.
# Prevents accidental or unauthorized account deletion.


class DeleteAccountForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I understand this will permanently delete my account."
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "placeholder": "Enter your password to confirm"
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        pw = self.cleaned_data["password"]
        if not self.user.check_password(pw):
            raise forms.ValidationError("Password is incorrect.")
        return pw


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "id": "settings-email"
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        return email


class RoleChangeForm(forms.Form):
    role = forms.ChoiceField(choices=[])

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_roles = allowed_roles or []
        self.fields["role"].choices = [(r, r.title()) for r in self.allowed_roles]

    def clean_role(self):
        r = self.cleaned_data["role"]
        if r not in self.allowed_roles:
            raise forms.ValidationError("Invalid role selection.")
        return r

# ModelForm for creating/editing Requests.
# Used in create_request and modal editing.
# Handles basic validation + formatting.


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            "title",
            "description",
            "category",
            "city",
            "location_details",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter request title"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Add any details here",
                "rows": 4
            }),
            "category": forms.Select(attrs={
                "class": "form-control"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city"
            }),
            "location_details": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional: near shelter, library, community center, etc."
            }),
        }

    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()

        if not city:
            raise forms.ValidationError("City is required.")

        if len(city) < 2:
            raise forms.ValidationError("City must be at least 2 characters long.")

        if not re.fullmatch(r"[A-Za-z .'-]+", city):
            raise forms.ValidationError(
                "City can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return " ".join(word.capitalize() for word in city.split())

# ModelForm for creating/editing Offers.
# Includes:
# - title length validation (max 60 chars)
# - city validation (max 25 chars)
# - optional image validation (size/type)
#
# NOTE:
# Image uploads are handled separately in views (multiple images support).


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            "title",
            "description",
            "category",
            "city",
            "location_details",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter offered item title",
                "id": "offer-title",
                "maxlength": "60",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Add any details here",
                "rows": 4
            }),
            "category": forms.Select(attrs={
                "class": "form-control"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter city",
                "id": "offer-city",
                "maxlength": "25",
            }),
            "location_details": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional: shelter, library, church, community center, etc."
            }),
        }

    def clean_offer_photo(self):
        photo = self.cleaned_data.get("offer_photo")

        if not photo:
            return photo

        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Photo must be smaller than 5MB.")

        valid_types = ["image/jpeg", "image/png", "image/webp"]
        if hasattr(photo, "content_type") and photo.content_type not in valid_types:
            raise forms.ValidationError("Upload a JPG, PNG, or WEBP image.")

        return photo

    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()

        if not city:
            raise forms.ValidationError("City is required.")

        if len(city) < 2:
            raise forms.ValidationError("City must be at least 2 characters long.")

        if len(city) > 25:
            raise forms.ValidationError("City cannot exceed 25 characters.")

        if not re.fullmatch(r"[A-Za-z\s\-'\.]+", city):
            raise forms.ValidationError("City can only contain letters, spaces, apostrophes, periods, and hyphens.")

        return " ".join(word.capitalize() for word in city.split())

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()

        if not title:
            raise forms.ValidationError("Title is required.")
        if len(title) < 2:
            raise forms.ValidationError("Title must be at least 2 characters long.")
        if len(title) > 60:
            raise forms.ValidationError("Title cannot exceed 60 characters.")

        return title

class AdminAccountEditForm(forms.Form):
    display_username = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.ChoiceField(choices=STATE_CHOICES, required=False)
    role = forms.ChoiceField(
        choices=[
            ("unhoused", "Unhoused"),
            ("volunteer", "Volunteer"),
            ("admin", "Admin"),
        ],
        required=True
    )

    def __init__(self, *args, profile: Profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile
        self.user = profile.user

    def clean_display_username(self):
        username = self.cleaned_data["display_username"].strip()

        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
        if any(ch not in allowed for ch in username):
            raise forms.ValidationError("Username can only use letters, numbers, _, -, and .")

        qs = Profile.objects.filter(display_username__iexact=username).exclude(pk=self.profile.pk)
        if qs.exists():
            raise forms.ValidationError("That username is already taken.")

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        qs = User.objects.filter(username__iexact=email).exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()

        if not first_name:
            return first_name

        if len(first_name) < 2:
            raise forms.ValidationError("First name must be at least 2 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", first_name):
            raise forms.ValidationError(
                "First name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()

        if not last_name:
            return last_name

        if len(last_name) < 2:
            raise forms.ValidationError("Last name must be at least 2 characters.")

        if not re.fullmatch(r"[A-Za-z .'-]+", last_name):
            raise forms.ValidationError(
                "Last name can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return last_name

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()

        if not phone:
            return phone

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Enter a valid phone number.")

        return digits

    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()

        if not city:
            return city

        if len(city) < 2:
            raise forms.ValidationError("Enter a valid city.")

        if not re.fullmatch(r"[A-Za-z .'-]+", city):
            raise forms.ValidationError(
                "City can only contain letters, spaces, apostrophes, hyphens, and periods."
            )

        return city

    def clean_state(self):
        state = self.cleaned_data.get("state", "").strip()

        if not state:
            return state

        if state not in VALID_STATE_VALUES:
            raise forms.ValidationError("Please select a valid state.")

        return state

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in {"unhoused", "volunteer", "admin"}:
            raise forms.ValidationError("Invalid role selection.")
        return role