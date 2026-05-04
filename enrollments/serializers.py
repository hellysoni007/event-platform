from rest_framework import serializers

from enrollments.models import Enrollment
from events.serializers import EventSerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "event", "status", "created_at", "updated_at"]
