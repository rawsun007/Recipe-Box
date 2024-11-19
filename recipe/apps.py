from django.apps import AppConfig




class RecipeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipe'

    def ready(self):
        import recipe.signals