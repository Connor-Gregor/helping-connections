from django import forms
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ("unhoused", "Unhoused"),
    ("volunteer", "Volunteer"),
]

class RegisterForm(forms.Form):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    # existing password match check
    def clean(self):
        cleaned = super().clean()

        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match")

        return cleaned

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)