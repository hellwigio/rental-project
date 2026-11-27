from django.conf import settings
from django.db import models


class SearchEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    keyword = models.CharField(max_length=200, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ListingView(models.Model):
    listing = models.ForeignKey("listings.Listing", related_name="visits", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
