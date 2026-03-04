from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Thread, Message, ThreadReadState
from .services import get_or_create_dm_thread
from .forms import NewThreadForm

def thread_display_name(thread, viewer):
    other_users = thread.participants.exclude(pk=viewer.pk).select_related("profile")
    names = []
    for u in other_users:
        display = None
        if hasattr(u, "profile") and u.profile.display_username:
            display = u.profile.display_username
        if not display:
            display = getattr(u, "email", "") or getattr(u, "username", "") or f"User {u.pk}"
        names.append(display)
    return ", ".join(names) if names else "Just you"

@login_required
def inbox(request):
    threads = (
        Thread.objects
        .filter(participants=request.user)
        .prefetch_related("participants__profile")
        .order_by("-updated_at")
    )

    thread_data = []

    for t in threads:
        other_users = t.participants.exclude(pk=request.user.pk)

        names = []
        for u in other_users:
            display = None
            if hasattr(u, "profile") and u.profile.display_username:
                display = u.profile.display_username
            if not display:
                display = getattr(u, "email", "") or getattr(u, "username", "") or f"User {u.pk}"
            names.append(display)

        thread_data.append({
            "thread": t,
            "display_name": ", ".join(names) if names else "Just you"
        })

    return render(request, "messaging/inbox.html", {
        "thread_data": thread_data
    })

@login_required
def thread_detail(request, thread_id):
    thread = get_object_or_404(
        Thread.objects.prefetch_related("participants__profile"),
        pk=thread_id
    )

    if not thread.participants.filter(pk=request.user.pk).exists():
        return redirect("messaging:inbox")

    display_name = thread_display_name(thread, request.user)

    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if body:
            Message.objects.create(thread=thread, sender=request.user, body=body)
            thread.updated_at = timezone.now()
            thread.save(update_fields=["updated_at"])

        ThreadReadState.objects.update_or_create(
            thread=thread, user=request.user, defaults={"last_read_at": timezone.now()}
        )
        return redirect("messaging:thread_detail", thread_id=thread.id)

    ThreadReadState.objects.update_or_create(
        thread=thread, user=request.user, defaults={"last_read_at": timezone.now()}
    )

    messages = thread.messages.select_related("sender").all()

    return render(request, "messaging/thread_detail.html", {
        "thread": thread,
        "messages": messages,
        "display_name": display_name,
    })

@login_required
def start_dm(request, user_id):
    # If you want to message someone from a profile card, etc.
    other = get_object_or_404(request.user.__class__, pk=user_id)
    if other.pk == request.user.pk:
        return redirect("messaging:inbox")
    thread = get_or_create_dm_thread(request.user, other)
    return redirect("messaging:thread_detail", thread_id=thread.id)

@login_required
def new_thread(request):
    if request.method == "POST":
        form = NewThreadForm(request.POST, user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data["recipient"]
            thread = get_or_create_dm_thread(request.user, recipient)
            return redirect("messaging:thread_detail", thread_id=thread.id)
    else:
        form = NewThreadForm(user=request.user)

    return render(request, "messaging/new_thread.html", {"form": form})