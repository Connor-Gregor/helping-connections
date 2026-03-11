from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Role(models.Model):
    # Name will be like unhoused, donor, and volunteer
    # If we want to combine donor and volunteer thats fine, we can probably then just
    # add it into the profile model and remove this model entirely
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)
    display_username = models.CharField(max_length=30, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=120, blank=True)
    address_line2 = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=60, blank=True)
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


class Request(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLAIMED = "claimed"
    STATUS_FULFILLED = "fulfilled"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLAIMED, "Claimed"),
        (STATUS_FULFILLED, "Fulfilled"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    CATEGORY_FOOD = "food"
    CATEGORY_CLOTHING = "clothing"
    CATEGORY_BLANKETS = "blankets"
    CATEGORY_HYGIENE = "hygiene"
    CATEGORY_TRANSPORT = "transport"
    CATEGORY_MEDICAL = "medical"

    CATEGORY_CHOICES = [
        (CATEGORY_FOOD, "Food"),
        (CATEGORY_CLOTHING, "Clothing"),
        (CATEGORY_BLANKETS, "Blankets / Bedding"),
        (CATEGORY_HYGIENE, "Hygiene Items"),
        (CATEGORY_TRANSPORT, "Transportation"),
        (CATEGORY_MEDICAL, "Medical Supplies"),
    ]

    requester = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="requests_made"
    )
    claimed_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests_claimed"
    )

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    city = models.CharField(max_length=60)
    location_details = models.CharField(max_length=150, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #This makes requests show up by newest first, obviously this will be tweaked later in a future sprint once
    # we sort requests by location, time, or type of request
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"