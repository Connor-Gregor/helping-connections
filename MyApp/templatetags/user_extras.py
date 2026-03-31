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


@register.filter
def role_name(user):
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None)
    return getattr(role, "name", "") or ""


@register.simple_tag
def dashboard_url(user):
    if not user.is_authenticated:
        return "home"

    role = getattr(getattr(user, "profile", None), "role", None)
    role_name = getattr(role, "name", None)

    if role_name == "volunteer":
        return "volunteer"
    elif role_name == "unhoused":
        return "unhoused"
    elif role_name == "admin":
        return "admin_dashboard"  # change if needed

    return "map"
