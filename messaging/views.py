from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q

from .models import Thread, Message, ThreadReadState
from .services import get_or_create_dm_thread
from .forms import NewThreadForm


# =========================================
# Messaging Views
# =========================================
# This file handles the direct-message workflow for Helping Connections.
#
# Includes:
# - inbox thread list
# - thread detail / send message
# - starting a DM from another page
# - creating a new thread
# - deleting one or all threads from a user's inbox
#
# NOTE:
# Threads are shared conversations, but deleting a thread from inbox only
# removes the current user from that thread unless no participants remain.
# =========================================


# Builds the display name shown to the current viewer for a thread.
# In a 1-on-1 thread this is usually the other person's display username.
# In a multi-user thread it joins the names of everyone except the viewer.
def thread_display_name(thread, viewer):
    other_users = thread.participants.exclude(pk=viewer.pk).select_related("profile")
    names = []

    for u in other_users:
        display = None

        # Prefer profile display_username when available because it is the
        # user-facing identity used throughout the app.
        if hasattr(u, "profile") and u.profile.display_username:
            display = u.profile.display_username

        # Fall back to email / username so the thread still has a usable label
        # even if profile data is incomplete.
        if not display:
            display = getattr(u, "email", "") or getattr(u, "username", "") or f"User {u.pk}"

        names.append(display)

    return ", ".join(names) if names else "Just you"

#  For current DM flows, return the first participant who is not the viewer.
#   This lets templates show a profile photo / fallback avatar for the inbox sidebar.
def thread_other_user(thread, viewer):

    return (
        thread.participants
            .exclude(pk=viewer.pk)
            .select_related("profile")
            .first()
    )

# Shows all threads for the current user along with:
# - thread display name
# - unread message count
# - most recent message
#
# Unread count here is message-based within each thread, not just a simple
# "thread is unread" boolean.
def build_thread_sidebar_data(viewer):
    threads = (
        Thread.objects
            .filter(participants=viewer)
            .prefetch_related("participants__profile", "messages__sender__profile")
            .order_by("-updated_at")
    )

    thread_data = []

    for t in threads:

        # Reuse the same display-name logic used elsewhere so the inbox stays
        # consistent with thread detail and DM creation flows.
        display_name = thread_display_name(t, viewer)
        other_user = thread_other_user(t, viewer)

        # Read state tracks the most recent time this user viewed the thread.
        read_state = ThreadReadState.objects.filter(
            thread=t,
            user=viewer
        ).first()

        # Only unread messages from OTHER users should count as unread.
        unread_qs = t.messages.exclude(sender=viewer)

        if read_state:
            unread_qs = unread_qs.filter(created_at__gt=read_state.last_read_at)

        unread_count = unread_qs.count()
        last_message = t.messages.order_by("-created_at").first()

        thread_data.append({
            "thread": t,
            "display_name": display_name,
            "other_user": other_user,
            "unread_count": unread_count,
            "last_message": last_message,
        })

    return thread_data


@login_required
def inbox(request):
    thread_data = build_thread_sidebar_data(request.user)

    return render(request, "messaging/inbox.html", {
        "thread_data": thread_data,
        "selected_thread_id": None,
    })


# Thread detail view:
# - displays all messages in one thread
# - allows the current user to send a new message
# - marks the thread as read when opened or after sending
#
# Security rule:
# user must be a participant in the thread.
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

        # updated_at is used to keep active threads higher in the inbox list.
        thread.updated_at = timezone.now()
        thread.save(update_fields=["updated_at"])

        # Sender has effectively read the thread up to the message they just sent.
        ThreadReadState.objects.update_or_create(
            thread=thread,
            user=request.user,
            defaults={"last_read_at": timezone.now()}
        )

        messages.success(request, "Message sent.")
        return redirect("messaging:thread_detail", thread_id=thread.id)

    # Opening a thread marks it as read for the current user.
    ThreadReadState.objects.update_or_create(
        thread=thread, user=request.user, defaults={"last_read_at": timezone.now()}
    )

    chat_messages = thread.messages.select_related("sender").order_by("created_at")
    thread_data = build_thread_sidebar_data(request.user)
    selected_other_user = thread_other_user(thread, request.user)

    return render(request, "messaging/thread_detail.html", {
        "thread": thread,
        "chat_messages": chat_messages,
        "display_name": display_name,
        "thread_data": thread_data,
        "selected_thread_id": thread.id,
        "selected_other_user": selected_other_user,
    })


# Starts a direct-message flow from elsewhere in the app.
#
# Important behavior:
# - prevents messaging yourself
# - reuses an existing 1-on-1 thread if one already exists
# - otherwise redirects to the new-thread page with a preselected recipient
#
# This avoids duplicate DM threads between the same two users.
@login_required
def start_dm(request, user_id):
    other = get_object_or_404(request.user.__class__, pk=user_id)

    if other.pk == request.user.pk:
        return redirect("messaging:inbox")

    existing_thread = (
        Thread.objects
            .annotate(
            total_participants=Count("participants", distinct=True),
            matched_participants=Count(
                "participants",
                filter=Q(participants=request.user) | Q(participants=other),
                distinct=True,
            ),
        )
            .filter(total_participants=2, matched_participants=2)
            .order_by("id")
            .first()
    )

    if existing_thread:
        return redirect("messaging:thread_detail", thread_id=existing_thread.id)

    return redirect(f"{reverse('messaging:new_thread')}?recipient={other.id}")


# New thread view:
# Creates the first message in a DM thread.
#
# Uses get_or_create_dm_thread() so we do not accidentally duplicate
# conversations if one already exists.
#
# Also supports redirecting back to paginated offer/request pages when the
# message form was opened from a modal instead of from the inbox directly.
@login_required
def new_thread(request):
    initial_recipient = request.GET.get("recipient")

    if request.method == "POST":
        form = NewThreadForm(request.POST, user=request.user)
        if form.is_valid():
            recipient = form.cleaned_data["recipient"]
            body = form.cleaned_data["body"].strip()

            if not body:
                messages.error(request, "Message cannot be empty.")
                return render(request, "messaging/new_thread.html", {"form": form})

            thread = get_or_create_dm_thread(request.user, recipient)

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

            return_to = request.POST.get("return_to")
            return_page_number = request.POST.get("return_page_number", "1")
            return_query = (request.POST.get("return_query") or "").strip()

            if return_to == "available_offers":
                if return_query:
                    return redirect(f"{reverse('available_offers')}?{return_query}")
                return redirect(f"{reverse('available_offers')}?page={return_page_number}")

            if return_to == "my_offers":
                if return_query:
                    return redirect(f"{reverse('my_offers')}?{return_query}")
                return redirect(f"{reverse('my_offers')}?page={return_page_number}")

            if return_to == "volunteer_requests":
                if return_query:
                    return redirect(f"{reverse('volunteer_requests')}?{return_query}")
                return redirect(f"{reverse('volunteer_requests')}?page={return_page_number}")

            if return_to == "volunteer":
                if return_query:
                    return redirect(f"{reverse('volunteer')}?{return_query}")
                return redirect("volunteer")

            if return_to == "unhoused":
                if return_query:
                    return redirect(f"{reverse('unhoused')}?{return_query}")
                return redirect("unhoused")

            return redirect("messaging:thread_detail", thread_id=thread.id)
    else:
        form = NewThreadForm(
            user=request.user,
            initial_recipient_id=initial_recipient
        )

    return render(request, "messaging/new_thread.html", {"form": form})


# Removes a single thread from the current user's inbox.
#
# Important:
# This is not always a hard delete.
# We remove only the current user from participants.
# The thread is deleted from the database only if no participants remain.
@login_required
def delete_thread(request, thread_id):
    if request.method != "POST":
        return redirect("messaging:inbox")

    thread = get_object_or_404(Thread, pk=thread_id)

    if not thread.participants.filter(pk=request.user.pk).exists():
        messages.error(request, "You do not have permission to delete this thread.")
        return redirect("messaging:inbox")

    thread.participants.remove(request.user)

    # Clean up per-user read tracking once the user leaves the conversation.
    ThreadReadState.objects.filter(thread=thread, user=request.user).delete()

    if thread.participants.count() == 0:
        thread.delete()

    messages.success(request, "Thread deleted from your inbox.")
    return redirect("messaging:inbox")


# Removes all threads from the current user's inbox using the same logic as
# delete_thread(): remove current user first, hard-delete only if thread
# becomes orphaned.
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