# messaging/forms.py
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class NewThreadForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Send to",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # exclude yourself
        self.fields["recipient"].queryset = User.objects.exclude(pk=user.pk).order_by("id")