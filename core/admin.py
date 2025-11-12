from django.contrib import admin
from .models import (
    UserPantry, Recipe, 
    ShoppingList,FoodWasteRecord, ShoppingListItem, 
    ImageProcessingJob, RecipeIngredient
) 

admin.site.register(UserPantry)
admin.site.register(Recipe)
admin.site.register(ShoppingList)
admin.site.register(ShoppingListItem)
# admin.site.register(ConsumptionRecord)
admin.site.register(FoodWasteRecord)
admin.site.register(ImageProcessingJob)
admin.site.register(RecipeIngredient)

