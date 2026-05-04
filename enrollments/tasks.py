from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from enrollments.models import Enrollment


@shared_task(bind=True, max_retries=3)
def send_enrollment_followup(self, enrollment_id: int):
    enrollment = Enrollment.objects.select_related("seeker", "event").filter(id=enrollment_id).first()
    if not enrollment or enrollment.status != "ENROLLED":
        return
    send_mail(
        subject="Enrollment follow-up",
        message=f"Thanks for enrolling in {enrollment.event.title}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[enrollment.seeker.email],
    )


@shared_task(bind=True, max_retries=3)
def send_event_reminder(self, enrollment_id: int):
    enrollment = Enrollment.objects.select_related("seeker", "event").filter(id=enrollment_id).first()
    if not enrollment or enrollment.status != "ENROLLED":
        return
    send_mail(
        subject="Event reminder",
        message=f"Reminder: {enrollment.event.title} starts in one hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[enrollment.seeker.email],
    )
