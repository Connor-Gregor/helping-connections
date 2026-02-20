from django import template

register = template.Library()

@register.filter
def initials(user):
    """
    Returns two-letter initials for the logged-in user.
    Uses first/last name if available, otherwise falls back to username.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return ""

    first = (getattr(user, "first_name", "") or "").strip()
    last = (getattr(user, "last_name", "") or "").strip()

    if first or last:
        return (first[:1] + last[:1]).upper()

    username = (getattr(user, "username", "") or "").strip()
    return username[:2].upper()