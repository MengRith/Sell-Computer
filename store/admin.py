from django.contrib import admin
from .models import Product, Category, Brand  # whatever your models are
# Username = admin
# Email = mkeosovannarith@gmail.com
# Password = abc123


# Register your models here.

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Brand)