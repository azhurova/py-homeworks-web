from rest_framework.viewsets import ModelViewSet

from logistic.models import Product, Stock
from logistic.serializers import ProductSerializer, StockSerializer


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ['title']
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title']


class StockViewSet(ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    filterset_fields = ['address', 'products']
    search_fields = ['address', 'products__title']
    ordering_fields = ['id', 'address']
