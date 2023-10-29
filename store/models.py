from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from autoslug import AutoSlugField
from uuid import uuid4


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        editable=False,
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Category(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(unique=True, populate_from="title")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    unit_price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(1)]
    )
    description = models.TextField(null=True, blank=True)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to="store/image")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._meta.get_field("slug").pre_save(self, False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def rating(self):
        return self.review.aggregate(Avg("rating"))["rating__avg"] or 0


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [["cart", "product"]]


class Order(models.Model):
    PAYPAL = "P"
    CARD = "C"
    PAYMENT_METHOD = [(PAYPAL, "Paypal"), (CARD, "Card")]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=1, default="", choices=PAYMENT_METHOD)
    street_address = models.CharField(max_length=255)
    zipcode = models.CharField(max_length=5)
    city = models.CharField(max_length=255)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField()


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="review"
    )
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "product"]]
