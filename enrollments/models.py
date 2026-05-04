from django.contrib.auth.models import User
from django.db import models

from events.models import Event


class EnrollmentStatus(models.TextChoices):
    ENROLLED = "ENROLLED", "Enrolled"
    CANCELED = "CANCELED", "Canceled"


class Enrollment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="enrollments")
    seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ENROLLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "seeker"], name="uniq_event_seeker_enrollment")
        ]
        indexes = [
            models.Index(fields=["seeker", "status"]),
            models.Index(fields=["event", "status"]),
        ]
