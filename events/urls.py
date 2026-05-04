from django.urls import path

from events.views import EventViewSet

event_list = EventViewSet.as_view({"get": "list", "post": "create"})
event_detail = EventViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})
event_mine = EventViewSet.as_view({"get": "mine"})

urlpatterns = [
    path("events", event_list, name="event-list"),
    path("events/mine", event_mine, name="event-mine"),
    path("events/<int:pk>", event_detail, name="event-detail"),
]
