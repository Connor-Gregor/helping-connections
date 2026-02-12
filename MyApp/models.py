from django.conf import settings
from django.db import models

class Role(models.Model):
    # Name will be like unhoused, donor, and volunteer
    # If we want to combine donor and volunteer thats fine, we can probably then just
    # add it into the profile model and remove this model entirely
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    roles = models.ManyToManyField(Role, blank=True)

    def __str__(self):
        return f"Profile: {self.user.username}"

