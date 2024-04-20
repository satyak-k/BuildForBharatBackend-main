from django.contrib import admin
from . import models


# Register your models here.
@admin.register(models.User, models.SellerGST, models.Catalogue, models.ProductCategory, models.Product, models.ProductDetails)
class APIModelsAdmin(admin.ModelAdmin):
    pass
