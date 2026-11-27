from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from ..models import Review
from ..serializers import ReviewSerializer
from ..services import leave_review


class Reviews(ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Review.objects.filter(booking__listing__is_active=True).order_by("-pk")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {"booking__listing": ["exact"]}

    def perform_create(self, serializer):
        serializer.instance = leave_review(self.request.user, **serializer.validated_data)
