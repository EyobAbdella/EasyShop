from django.urls import path
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()
router.register("products", views.ProductViewSet)
router.register("category", views.CategoryViewSet)
router.register("carts", views.CartViewSet)
router.register("orders", views.OrderViewSet, basename="order")


product_router = routers.NestedDefaultRouter(router, "products", lookup="product")
product_router.register("reviews", views.ReviewViewSet, basename="product-review")

carts_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
carts_router.register("items", views.CartItemViewSet, basename="cart-items")


urlpatterns = router.urls + carts_router.urls + product_router.urls
