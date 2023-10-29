from django.contrib import admin
from .models import Category, Order, Product, Review

admin.site.register(Category)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "unit_price", "category"]
    list_editable = ["unit_price"]
    search_fields = ["title"]
    list_select_related = ["category"]
    list_filter = ["category", "last_update"]


@admin.register(Review)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "review", "rating", "created_at"]
    list_editable = ["user"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "customer",
        "is_paid",
        "is_delivered",
        "street_address",
        "city",
        "zipcode",
        "created_at",
    ]

    list_editable = ["is_delivered"]
    list_filter = ["is_paid", "is_delivered"]
