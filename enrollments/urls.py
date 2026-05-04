from django.urls import path

from enrollments.views import (
    CancelEnrollmentView,
    EnrollEventView,
    PastEnrollmentsView,
    UpcomingEnrollmentsView,
)

urlpatterns = [
    path("events/<int:event_id>/enroll", EnrollEventView.as_view(), name="event-enroll"),
    path("enrollments/<int:enrollment_id>/cancel", CancelEnrollmentView.as_view(), name="enrollment-cancel"),
    path("enrollments/upcoming", UpcomingEnrollmentsView.as_view(), name="enrollments-upcoming"),
    path("enrollments/past", PastEnrollmentsView.as_view(), name="enrollments-past"),
]
