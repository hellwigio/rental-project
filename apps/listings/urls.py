from rest_framework.routers import SimpleRouter

from .views import Listings

router = SimpleRouter()
router.register("", Listings, basename="listing")
urlpatterns = router.urls
