from messaging.models import Thread, ThreadReadState


# This context processor provides the unread message count
# for the currently logged-in user.
#
# It is used globally (e.g., navbar/profile dropdown) to show
# how many conversation threads have unread messages.
# NOTE:
# This counts unread threads, not total unread messages.
# Each thread contributes at most 1 to the count.
def unread_messages(request):

    # If user is not logged in → no unread messages
    if not request.user.is_authenticated:
        return {"unread_message_count": 0}

    # Get all threads where the user is a participant
    threads = Thread.objects.filter(participants=request.user)

    unread_count = 0

    for thread in threads:

        # Get the most recent message in the thread
        last_message = thread.messages.order_by("-created_at").first()

        # If thread has no messages → skip
        if not last_message:
            continue

        # If the last message was sent by the current user,
        # it should not count as unread
        if last_message.sender_id == request.user.id:
            continue

        # Get the user's read state for this thread
        # (tracks the last time they viewed/read the thread)
        read_state = ThreadReadState.objects.filter(
            thread=thread,
            user=request.user
        ).first()

        # If:
        # - no read state exists (never opened thread), OR
        # - last message is newer than last_read_at
        # → count as unread
        if read_state is None or last_message.created_at > read_state.last_read_at:
            unread_count += 1

    # Returned as a dictionary so Django can inject it into templates
    return {"unread_message_count": unread_count}