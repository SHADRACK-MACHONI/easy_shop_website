from django.db import models
from django.contrib.auth.models import User
from .product import Product

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    available = models.BooleanField(default=True)

    def _str_(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),                # Order placed, waiting to be prepared
        ('Out for Delivery', 'Out for Delivery'),  # Dispatched from store
        ('Delivered', 'Delivered'),           # Customer confirmed delivery
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    house = models.CharField(max_length=100)
    room = models.CharField(max_length=100)
    payment_confirmed = models.BooleanField(default=False)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    admin_seen = models.BooleanField(default=False),

    def _str_(self):
        return f"Order for {self.product.name} by {self.customer_name}"
