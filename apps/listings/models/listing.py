from django.conf import settings
from django.db import models


class Listing(models.Model):
    class HousingType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        HOUSE = "house", "House"
        STUDIO = "studio", "Studio"
        ROOM = "room", "Room"
        OTHER = "other", "Other"

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="listings",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    city = models.CharField(max_length=120)
    district = models.CharField(max_length=120, blank=True)
    nightly_price = models.DecimalField(max_digits=10, decimal_places=2)
    rooms = models.PositiveSmallIntegerField()
    housing_type = models.CharField(max_length=12, choices=HousingType)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nightly_price__gt=0),
                name="listing_positive_price",
            ),
            models.CheckConstraint(
                condition=models.Q(rooms__gte=1),
                name="listing_positive_rooms",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "created_at"], name="listing_active_created_idx"),
            models.Index(fields=["is_active", "nightly_price"], name="listing_active_price_idx"),
        ]

    def __str__(self):
        return self.title
