from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ActiveEventQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    language = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    enrolled_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_events")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveEventQuerySet.as_manager()
    all_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["starts_at"]),
            models.Index(fields=["language"]),
            models.Index(fields=["location"]),
            models.Index(fields=["created_by", "starts_at"]),
            models.Index(fields=["is_deleted", "starts_at"]),
        ]
        ordering = ["starts_at"]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("Event end time must be after start time.")
        if self.capacity is not None and self.capacity <= 0:
            raise ValidationError("Capacity must be greater than zero.")
        if timezone.is_naive(self.starts_at) or timezone.is_naive(self.ends_at):
            raise ValidationError("Datetime fields must be timezone-aware UTC values.")

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
