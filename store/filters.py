from django_filters import rest_framework, filters
from .models import Product


class ProductFilter(rest_framework.FilterSet):
    category = filters.CharFilter(field_name="category__title", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ["category"]
