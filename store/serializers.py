from django.db import transaction
from django.db.models import F, Sum
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import (
    Cart,
    CartItem,
    Category,
    Customer,
    Order,
    Product,
    OrderItem,
    Review,
)


class CustomerSerializer(ModelSerializer):
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Customer
        fields = ["user_id", "email", "first_name", "last_name"]


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


class ProductSerializer(ModelSerializer):
    category = CategorySerializer()
    rating = serializers.IntegerField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else None

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "unit_price",
            "description",
            "image",
            "rating",
            "inventory",
            "last_update",
        ]


class CartItemSerializer(ModelSerializer):
    product = ProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price"]


class CartSerializer(ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items"]


class AddCartItemSerializer(ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No product with the given ID.")
        return value

    def save(self, **kwargs):
        cart_id = self.context.get("cart_id")
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data
            )
        return self.instance

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]


class UpdateCartItemSerializer(ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class OrderItemSerializer(ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderSerializer(ModelSerializer):
    customer = CustomerSerializer()
    items = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return obj.items.aggregate(
            total_price=Sum(F("product__unit_price") * F("quantity"))
        )["total_price"]

    class Meta:
        model = Order
        fields = [
            "id",
            "created_at",
            "customer",
            "payment_method",
            "street_address",
            "city",
            "zipcode",
            "is_paid",
            "is_delivered",
            "items",
            "total_price",
        ]


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    street_address = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=255)
    zipcode = serializers.CharField(max_length=5)

    def validate_cart_id(self, value):
        if not Cart.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No cart with the given ID.")
        elif CartItem.objects.filter(cart_id=value).count() == 0:
            raise serializers.ValidationError("The cart is empty.")
        return value

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data.get("cart_id")
            user_id = self.context.get("user_id")
            street_address = self.validated_data["street_address"]
            city = self.validated_data["city"]
            zipcode = self.validated_data["zipcode"]
            order = Order.objects.create(
                customer_id=user_id,
                street_address=street_address,
                city=city,
                zipcode=zipcode,
            )
            cart_item = CartItem.objects.filter(cart_id=cart_id).select_related(
                "product"
            )
            order_items = [
                OrderItem(order=order, product=item.product, quantity=item.quantity)
                for item in cart_item
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(pk=cart_id).delete()
            return order


class ReviewSerializer(ModelSerializer):
    user = CustomerSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "review", "rating", "created_at"]

    def create(self, validated_data):
        user_id = self.context["user_id"]
        product_id = self.context["product_id"]
        return Review.objects.create(
            user_id=user_id, product_id=product_id, **validated_data
        )
