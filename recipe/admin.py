from django.contrib import admin
from .models import CommunityRecipe, SavedRecipe, UserProfile

# Register your models here
admin.site.register(CommunityRecipe)
admin.site.register(SavedRecipe)
admin.site.register(UserProfile)
