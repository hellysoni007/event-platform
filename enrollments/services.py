from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status

from accounts.models import UserRole
from core.error_codes import ErrorCodes
from core.exceptions import DomainError
from enrollments.models import Enrollment, EnrollmentStatus
from enrollments.tasks import send_enrollment_followup, send_event_reminder
from events.models import Event


def enroll_seeker(event_id: int, user):
    if not hasattr(user, "profile") or user.profile.role != UserRole.SEEKER:
        raise DomainError(
            detail="Seeker role required.",
            code=ErrorCodes.FORBIDDEN_ROLE,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    with transaction.atomic():
        event = Event.all_objects.select_for_update().filter(id=event_id).first()
        if not event or event.is_deleted:
            raise DomainError(
                detail="Event not found.",
                code=ErrorCodes.EVENT_NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if event.created_by_id == user.id:
            raise DomainError(
                detail="Cannot enroll in own event.",
                code=ErrorCodes.SELF_ENROLLMENT_FORBIDDEN,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if event.starts_at <= timezone.now():
            raise DomainError(
                detail="Cannot enroll in past or started event.",
                code=ErrorCodes.EVENT_ALREADY_STARTED,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        enrollment, created = Enrollment.objects.select_for_update().get_or_create(
            event=event,
            seeker=user,
            defaults={"status": EnrollmentStatus.ENROLLED},
        )
        if not created and enrollment.status == EnrollmentStatus.ENROLLED:
            raise DomainError(
                detail="Already enrolled.",
                code=ErrorCodes.ALREADY_ENROLLED,
                status_code=status.HTTP_409_CONFLICT,
            )

        if event.capacity is not None and event.enrolled_count >= event.capacity:
            raise DomainError(
                detail="Event is full.",
                code=ErrorCodes.EVENT_FULL,
                status_code=status.HTTP_409_CONFLICT,
            )

        if not created:
            enrollment.status = EnrollmentStatus.ENROLLED
            enrollment.save(update_fields=["status", "updated_at"])

        Event.all_objects.filter(id=event.id).update(enrolled_count=F("enrolled_count") + 1)
        enrollment.refresh_from_db()

    send_enrollment_followup.apply_async(args=[enrollment.id], eta=timezone.now() + timedelta(hours=1))
    send_event_reminder.apply_async(args=[enrollment.id], eta=event.starts_at - timedelta(hours=1))
    return enrollment


def cancel_enrollment(enrollment_id: int, user):
    with transaction.atomic():
        enrollment = (
            Enrollment.objects.select_for_update()
            .select_related("event")
            .filter(id=enrollment_id, seeker=user)
            .first()
        )
        if not enrollment:
            raise DomainError(
                detail="Enrollment not found.",
                code=ErrorCodes.EVENT_NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if enrollment.status == EnrollmentStatus.CANCELED:
            return enrollment

        enrollment.status = EnrollmentStatus.CANCELED
        enrollment.save(update_fields=["status", "updated_at"])
        Event.all_objects.filter(id=enrollment.event_id).update(enrolled_count=F("enrolled_count") - 1)
        enrollment.refresh_from_db()
        return enrollment
