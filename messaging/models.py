from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Thread(models.Model):
    participants = models.ManyToManyField(User, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def other_participants(self, user):
        return self.participants.exclude(pk=user.pk)

    def display_name_for(self, user):
        """
        For the inbox: show the other participant(s) names.
        Uses Profile.display_username if present, otherwise falls back to email/username.
        """
        names = []
        for u in self.other_participants(user):
            # Try Profile.display_username
            display = ""
            if hasattr(u, "profile") and getattr(u.profile, "display_username", None):
                display = u.profile.display_username
            # Fallbacks
            if not display:
                display = getattr(u, "email", "") or getattr(u, "username", "") or f"User {u.pk}"
            names.append(display)

        return ", ".join(names) if names else "Just you"


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.id} (Thread {self.thread_id})"


class ThreadReadState(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="read_states")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="thread_reads")
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("thread", "user")]