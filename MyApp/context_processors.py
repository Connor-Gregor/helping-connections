from messaging.models import Thread, ThreadReadState


def unread_messages(request):
    if not request.user.is_authenticated:
        return {"unread_message_count": 0}

    threads = Thread.objects.filter(participants=request.user)

    unread_count = 0

    for thread in threads:
        last_message = thread.messages.order_by("-created_at").first()
        if not last_message:
            continue

        if last_message.sender_id == request.user.id:
            continue

        read_state = ThreadReadState.objects.filter(
            thread=thread,
            user=request.user
        ).first()

        if read_state is None or last_message.created_at > read_state.last_read_at:
            unread_count += 1

    return {"unread_message_count": unread_count}