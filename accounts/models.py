from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for the E-Commerce API."""

    email = models.EmailField(
        unique=True,
        help_text="User's unique email address."
    )