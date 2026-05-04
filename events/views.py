from django.db.models import Count, F, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.error_codes import ErrorCodes
from core.exceptions import DomainError
from events.models import Event
from events.permissions import IsEventOwner, IsFacilitatorOrReadOnly
from events.serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.active()
    permission_classes = [IsFacilitatorOrReadOnly & IsEventOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["location", "language"]
    search_fields = ["title", "description"]
    ordering_fields = ["starts_at", "created_at"]
    ordering = ["starts_at"]

    def get_permissions(self):
        if self.action in {"mine"}:
            return [IsAuthenticated()]
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        if self.action == "create":
            return [IsAuthenticated(), IsFacilitatorOrReadOnly()]
        return [IsAuthenticated(), IsFacilitatorOrReadOnly(), IsEventOwner()]

    def get_queryset(self):
        queryset = Event.objects.active()
        starts_after = self.request.query_params.get("starts_after")
        starts_before = self.request.query_params.get("starts_before")
        if starts_after:
            queryset = queryset.filter(starts_at__gte=starts_after)
        if starts_before:
            queryset = queryset.filter(starts_at__lte=starts_before)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(methods=["get"], detail=False, url_path="events/mine")
    def mine(self, request):
        queryset = (
            Event.objects.active()
            .filter(created_by=request.user)
            .annotate(total_enrollments=Count("enrollments", filter=Q(enrollments__status="ENROLLED")))
            .annotate(available_seats=F("capacity") - F("enrolled_count"))
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
from django.shortcuts import render

# Create your views here.
