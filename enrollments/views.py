from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from enrollments.models import Enrollment, EnrollmentStatus
from enrollments.serializers import EnrollmentSerializer
from enrollments.services import cancel_enrollment, enroll_seeker


class EnrollEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id: int):
        enrollment = enroll_seeker(event_id=event_id, user=request.user)
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, enrollment_id: int):
        enrollment = cancel_enrollment(enrollment_id=enrollment_id, user=request.user)
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpcomingEnrollmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Enrollment.objects.select_related("event")
            .filter(
                seeker=request.user,
                status=EnrollmentStatus.ENROLLED,
                event__starts_at__gt=timezone.now(),
                event__is_deleted=False,
            )
            .order_by("event__starts_at")
        )
        serializer = EnrollmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PastEnrollmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            Enrollment.objects.select_related("event")
            .filter(seeker=request.user, event__ends_at__lt=timezone.now(), event__is_deleted=False)
            .order_by("-event__ends_at")
        )
        serializer = EnrollmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
