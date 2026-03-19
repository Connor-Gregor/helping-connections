from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
        .prefetch_related("participants__profile", "messages__sender__profile")
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

        display_name = ", ".join(names) if names else "Just you"

        read_state = ThreadReadState.objects.filter(
            thread=t,
            user=request.user
        ).first()

        unread_qs = t.messages.exclude(sender=request.user)

        if read_state:
            unread_qs = unread_qs.filter(created_at__gt=read_state.last_read_at)

        unread_count = unread_qs.count()

        last_message = t.messages.order_by("-created_at").first()

        thread_data.append({
            "thread": t,
            "display_name": display_name,
            "unread_count": unread_count,
            "last_message": last_message,
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

        if not body:
            messages.error(request, "Message cannot be empty.")
            return redirect("messaging:thread_detail", thread_id=thread.id)

        Message.objects.create(thread=thread, sender=request.user, body=body)

        thread.updated_at = timezone.now()
        thread.save(update_fields=["updated_at"])

        ThreadReadState.objects.update_or_create(
            thread=thread,
            user=request.user,
            defaults={"last_read_at": timezone.now()}
        )

        messages.success(request, "Message sent.")
        return redirect("messaging:thread_detail", thread_id=thread.id)

    ThreadReadState.objects.update_or_create(
        thread=thread, user=request.user, defaults={"last_read_at": timezone.now()}
    )

    chat_messages = thread.messages.select_related("sender").all()

    return render(request, "messaging/thread_detail.html", {
        "thread": thread,
        "chat_messages": chat_messages,
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
            body = form.cleaned_data["body"].strip()

            thread = get_or_create_dm_thread(request.user, recipient)

            if body:
                Message.objects.create(
                    thread=thread,
                    sender=request.user,
                    body=body
                )
                thread.updated_at = timezone.now()
                thread.save(update_fields=["updated_at"])

            ThreadReadState.objects.update_or_create(
                thread=thread,
                user=request.user,
                defaults={"last_read_at": timezone.now()}
            )

            messages.success(request, "Message sent.")
            return redirect("messaging:thread_detail", thread_id=thread.id)
    else:
        form = NewThreadForm(user=request.user)

    return render(request, "messaging/new_thread.html", {"form": form})

@login_required
def delete_thread(request, thread_id):
    if request.method != "POST":
        return redirect("messaging:inbox")

    thread = get_object_or_404(Thread, pk=thread_id)

    if not thread.participants.filter(pk=request.user.pk).exists():
        messages.error(request, "You do not have permission to delete this thread.")
        return redirect("messaging:inbox")

    # Remove the current user from the conversation
    thread.participants.remove(request.user)

    # Clean up read state for this user
    ThreadReadState.objects.filter(thread=thread, user=request.user).delete()

    # If no participants remain, delete the whole thread
    if thread.participants.count() == 0:
        thread.delete()

    messages.success(request, "Thread deleted from your inbox.")
    return redirect("messaging:inbox")
@login_required
def delete_all_threads(request):
    if request.method != "POST":
        return redirect("messaging:inbox")

    threads = Thread.objects.filter(participants=request.user).distinct()

    deleted_count = threads.count()

    for thread in threads:
        thread.participants.remove(request.user)
        ThreadReadState.objects.filter(thread=thread, user=request.user).delete()

        if thread.participants.count() == 0:
            thread.delete()

    if deleted_count == 0:
        messages.info(request, "No threads to delete.")
    else:
        messages.success(request, f"{deleted_count} thread(s) deleted from your inbox.")

    return redirect("messaging:inbox")
