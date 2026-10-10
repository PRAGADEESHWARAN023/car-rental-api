from rest_framework.routers import DefaultRouter

from .views import CarViewSet

router = DefaultRouter()
router.register("cars", CarViewSet, basename="car")
urlpatterns = router.urls
