from django.db import transaction
from django.db.models import Count
from .models import Thread, ThreadReadState

@transaction.atomic
def get_or_create_dm_thread(user_a, user_b):
    existing = (
        Thread.objects
        .filter(participants=user_a)
        .filter(participants=user_b)
        .annotate(num_participants=Count("participants"))
        .filter(num_participants=2)
        .first()
    )
    if existing:
        return existing

    thread = Thread.objects.create()
    thread.participants.add(user_a, user_b)

    ThreadReadState.objects.get_or_create(thread=thread, user=user_a)
    ThreadReadState.objects.get_or_create(thread=thread, user=user_b)
    return thread