from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    SEEKER = "SEEKER", "Seeker"
    FACILITATOR = "FACILITATOR", "Facilitator"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=UserRole.choices)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} ({self.role})"


class OTPChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otp_challenges")
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    resend_count = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["expires_at"]),
        ]

    @classmethod
    def default_expiry(cls):
        return timezone.now() + timedelta(minutes=5)

    def is_expired(self):
        return timezone.now() >= self.expires_at
