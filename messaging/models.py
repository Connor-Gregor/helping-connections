from django.conf import settings
from django.db import models
from django.utils import timezone

# Use the project's configured user model instead of importing Django's User directly.
User = settings.AUTH_USER_MODEL


# Represents one conversation thread between participants.
#
# In this project, threads are primarily used for direct messaging.
# A thread can technically support multiple participants, but current UI flows
# mainly create 1-on-1 conversations.
#
# updated_at is important because inbox views sort by most recently active thread.
class Thread(models.Model):
    participants = models.ManyToManyField(User, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Returns all participants except the current viewer.
    # Useful for 1-on-1 thread labels and recipient display logic.
    def other_participants(self, user):
        return self.participants.exclude(pk=user.pk)

    # Builds the thread label shown in places like the inbox.
    # Prefer Profile.display_username because that is the app's user-facing name.
    # Fall back to email / username if profile data is missing.
    def display_name_for(self, user):
        """
        For the inbox: show the other participant(s) names.
        Uses Profile.display_username if present, otherwise falls back to email/username.
        """
        names = []
        for u in self.other_participants(user):
            # Try Profile.display_username first
            display = ""
            if hasattr(u, "profile") and getattr(u.profile, "display_username", None):
                display = u.profile.display_username

            # Fallbacks if profile/display name is missing
            if not display:
                display = getattr(u, "email", "") or getattr(u, "username", "") or f"User {u.pk}"

            names.append(display)

        return ", ".join(names) if names else "Just you"


# Represents one message inside a thread.
#
# Each message belongs to exactly one thread and has one sender.
# Messages are ordered oldest -> newest by default so thread detail pages
# render in normal chat order.
class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.id} (Thread {self.thread_id})"


# Tracks the last read timestamp for each user in each thread.
#
# This powers unread-thread / unread-message logic in the inbox and navbar.
# There should only be one read-state row per (thread, user) pair.
class ThreadReadState(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="read_states")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="thread_reads")
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Prevent duplicate read-state rows for the same user in the same thread.
        unique_together = [("thread", "user")]