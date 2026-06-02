from django.contrib import admin
from .models import Product, Category, Brand  # whatever your models are


# Register your models here.

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)