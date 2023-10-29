from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .models import Cart, CartItem, Category, Order, Product, Review
from .serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    CreateOrderSerializer,
    OrderSerializer,
    ProductSerializer,
    ReviewSerializer,
    UpdateCartItemSerializer,
)
from .filters import ProductFilter
from .pagination import DefaultPagination


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = Product.objects.select_related("category").order_by("pk").all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ["title"]
    pagination_class = DefaultPagination
    lookup_field = "slug"


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CartViewSet(ModelViewSet):
    http_method_names = ["post", "delete"]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete", "patch"]

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs["cart_pk"])

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def create(self, request, *args, **kwargs):
        serializer = AddCartItemSerializer(
            data=request.data, context={"cart_id": kwargs["cart_pk"]}
        )
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        serializer = CartItemSerializer(cart_item, context={"request": request})
        return Response(serializer.data)

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"], "request": self.request}


class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer_id=self.request.user.id).order_by(
            "-created_at"
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={"user_id": request.user.id},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_slug = self.kwargs["product_slug"]
        product = get_object_or_404(Product, slug=product_slug)
        return Review.objects.filter(product=product)

    def get_serializer_context(self):
        product_slug = self.kwargs["product_slug"]
        product = get_object_or_404(Product, slug=product_slug)
        return {
            "user_id": self.request.user.id,
            "product_id": product.id,
        }

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id != instance.user.user_id:
            return Response(
                {"error": "You don't have permission to update this post."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)
