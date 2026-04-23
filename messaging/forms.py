from django import forms
from django.contrib.auth import get_user_model

# Use Django's configured User model (supports custom user models)
User = get_user_model()


# =========================================
# Messaging Forms
# =========================================
# This form is used to:
# - start a new conversation (thread)
# - send the first message
#
# NOTE:
# - Only allows selecting other users (not yourself)
# - Supports pre-selecting a recipient (used by modal / "Message" buttons)
# =========================================
class NewThreadForm(forms.Form):

    # Dropdown field for choosing who to message
    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),  # set dynamically in __init__
        label="Send to",
    )

    # Text area for the message body
    body = forms.CharField(
        label="Message",
        max_length=500,
        error_messages={
            "max_length": "Messages cannot be longer than 500 characters.",
            "required": "Please enter a message.",
        },
        widget=forms.Textarea(attrs={
            "rows": 5,
            "placeholder": "Type your message here...",
            "maxlength": "500",
        })
    )

    def __init__(self, *args, user=None, initial_recipient_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit recipient choices:
        # - exclude current user (cannot message yourself)
        # - order for consistent dropdown display
        self.fields["recipient"].queryset = (
            User.objects.exclude(pk=user.pk).order_by("id")
        )

        # If a recipient ID is provided (e.g., from modal "Message" button),
        # automatically pre-select that user in the dropdown
        if initial_recipient_id:
            try:
                self.fields["recipient"].initial = User.objects.get(pk=initial_recipient_id)
            except User.DoesNotExist:
                # Fail silently if invalid ID is passed
                pass
