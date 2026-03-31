from django.db import transaction
from django.db.models import Count, Q
from .models import Thread, ThreadReadState


# =========================================
# Messaging Services
# =========================================
# Service-layer helpers for messaging workflows.
#
# This file exists so reusable messaging logic can stay outside views.
# That keeps views thinner and avoids duplicating thread-creation logic
# across inbox, modal messaging, and direct-message flows.
# =========================================


@transaction.atomic
def get_or_create_dm_thread(user_a, user_b):

    # Look for an existing thread that contains exactly these two users
    # and no one else.
    #
    # total_participants = total number of users in the thread
    # matched_participants = how many of those participants are user_a/user_b
    #
    # A valid 1-on-1 DM match must have:
    # - exactly 2 participants total
    # - both of them are the requested users
    existing = (
        Thread.objects
        .annotate(
            total_participants=Count("participants", distinct=True),
            matched_participants=Count(
                "participants",
                filter=Q(participants=user_a) | Q(participants=user_b),
                distinct=True,
            ),
        )
        .filter(total_participants=2, matched_participants=2)
        .order_by("id")
        .first()
    )

    # Reuse the existing direct-message thread so duplicate conversations
    # are not created between the same two users.
    if existing:
        return existing

    # Otherwise create a new thread and attach both participants.
    thread = Thread.objects.create()
    thread.participants.add(user_a, user_b)

    # Create read-state rows up front for both users so unread tracking
    # works immediately when messages start being exchanged.
    ThreadReadState.objects.get_or_create(thread=thread, user=user_a)
    ThreadReadState.objects.get_or_create(thread=thread, user=user_b)

    return thread
