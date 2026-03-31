from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

# =========================================
# Helping Connections - Models
# =========================================
# This file defines the main database structure for the app.
#
# Includes:
# - User profile + role assignment
# - Requests and Offers
# - Offer images
# - Reporting system
# - Email verification codes
#
# NOTE:
# Request and Offer share a similar lifecycle:
# open -> claimed -> fulfilled/cancelled


# Stores the app-specific role assigned to a user profile.
# Current roles are "volunteer" and "unhoused".
# Kept as a separate model so roles can be referenced consistently.

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# Extends Django's built-in User model with app-specific information.
# This is where we store:
# - role
# - display username
# - contact/location info
# - optional profile photo
#
# Most role checks in views/templates go through request.user.profile.

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

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Profile: {self.user.username}"

# Represents a help request created by an unhoused user.
#
# Key workflow:
# - requester creates request
# - volunteer can claim it
# - request can later be fulfilled or cancelled
#
# claimed_by / claimed_at track which volunteer is currently handling it.

class Request(models.Model):
    # Status values are reused across views, templates, and modal logic.
    # Keep these constants stable to avoid breaking role-based workflows and UI conditions.
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
    claimed_at = models.DateTimeField(null=True, blank=True)

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"

# Represents an offer created by a volunteer.
#
# Key workflow:
# - volunteer creates offer
# - unhoused user can claim it
# - offer can later be fulfilled or cancelled
#
# Structure intentionally mirrors Request for consistency across the app.

class Offer(models.Model):
    # Status values are reused across views, templates, and modal logic.
    # Keep these constants stable to avoid breaking role-based workflows and UI conditions.
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

    offered_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="offers_made"
    )
    claimed_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="offers_claimed"
    )
    claimed_at = models.DateTimeField(null=True, blank=True)

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"

# Stores multiple uploaded images for a single offer.
# The related_name="images" lets templates and views access them as offer.images.all().

class OfferImage(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="offer_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.offer.title}"

# Stores reports submitted against offers and/or the user who posted them.
# Used for moderation/review workflows.
#
# reporter = who submitted the report
# reported_user = the profile being reported
# offer = the offer involved in the report

class OfferReport(models.Model):
    REASON_INAPPROPRIATE = "inappropriate"
    REASON_UNSAFE = "unsafe"
    REASON_MISLEADING = "misleading"
    REASON_SPAM = "spam"
    REASON_HARASSMENT = "harassment"
    REASON_NOT_AS_DESCRIBED = "not_as_described"
    REASON_OTHER = "other"

    REASON_CHOICES = [
        (REASON_INAPPROPRIATE, "Inappropriate or offensive content"),
        (REASON_UNSAFE, "Suspicious or unsafe request/offer"),
        (REASON_MISLEADING, "Misleading or false information"),
        (REASON_SPAM, "Spam or repeated posts"),
        (REASON_HARASSMENT, "Harassment or abusive behavior"),
        (REASON_NOT_AS_DESCRIBED, "Item/request not as described"),
        (REASON_OTHER, "Other"),
    ]

    STATUS_OPEN = "open"
    STATUS_REVIEWED = "reviewed"
    STATUS_DISMISSED = "dismissed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_DISMISSED, "Dismissed"),
    ]

    reporter = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="offer_reports_made"
    )
    reported_user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="offer_reports_received"
    )
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Offer report on {self.offer.title} by {self.reporter}"

# Stores reports submitted against requests and/or the user who posted them.
# Separate from OfferReport so request moderation can evolve independently if needed.

class RequestReport(models.Model):
    REASON_INAPPROPRIATE = "inappropriate"
    REASON_UNSAFE = "unsafe"
    REASON_MISLEADING = "misleading"
    REASON_SPAM = "spam"
    REASON_HARASSMENT = "harassment"
    REASON_NOT_AS_DESCRIBED = "not_as_described"
    REASON_OTHER = "other"

    REASON_CHOICES = [
        (REASON_INAPPROPRIATE, "Inappropriate or offensive content"),
        (REASON_UNSAFE, "Suspicious or unsafe request/offer"),
        (REASON_MISLEADING, "Misleading or false information"),
        (REASON_SPAM, "Spam or repeated posts"),
        (REASON_HARASSMENT, "Harassment or abusive behavior"),
        (REASON_NOT_AS_DESCRIBED, "Item/request not as described"),
        (REASON_OTHER, "Other"),
    ]

    STATUS_OPEN = "open"
    STATUS_REVIEWED = "reviewed"
    STATUS_DISMISSED = "dismissed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_DISMISSED, "Dismissed"),
    ]

    reporter = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="request_reports_made"
    )
    reported_user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="request_reports_received"
    )
    request_item = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request report on {self.request_item.title} by {self.reporter}"

# Stores one-time verification codes used for:
# - initial account verification
# - email change verification
#
# verified=False means the code is still pending.
# expires_at controls when the code becomes invalid.

class EmailVerificationCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)

    # Returns True if the verification code is past its expiration time.
    def is_expired(self):
        return timezone.now() > self.expires_at

    # Helper for generating the default expiration window (10 minutes). Needs testing and further implementation
    @staticmethod
    def default_expiry():
        return timezone.now() + timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.email} - {self.code}"
