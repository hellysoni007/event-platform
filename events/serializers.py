from django.utils import timezone
from rest_framework import serializers

from events.models import Event


class EventSerializer(serializers.ModelSerializer):
    available_seats = serializers.SerializerMethodField()
    total_enrollments = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "language",
            "location",
            "starts_at",
            "ends_at",
            "capacity",
            "enrolled_count",
            "available_seats",
            "total_enrollments",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "enrolled_count", "created_at", "updated_at"]

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        capacity = attrs.get("capacity", getattr(self.instance, "capacity", None))

        if starts_at and timezone.is_naive(starts_at):
            raise serializers.ValidationError("starts_at must include timezone.")
        if ends_at and timezone.is_naive(ends_at):
            raise serializers.ValidationError("ends_at must include timezone.")
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError("ends_at must be greater than starts_at.")
        if capacity is not None and capacity <= 0:
            raise serializers.ValidationError("capacity must be greater than zero.")
        return attrs

    def get_available_seats(self, obj):
        if obj.capacity is None:
            return None
        return max(obj.capacity - obj.enrolled_count, 0)
