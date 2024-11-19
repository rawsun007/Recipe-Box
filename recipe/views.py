# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from .models import CommunityRecipe, SavedRecipe, UserProfile
from .utils import upload_image_to_cloudinary,fetch_recipes
import re  # For sanitizing public IDs
import requests
import cloudinary
import cloudinary.uploader
from django.contrib.auth import get_user_model
User = get_user_model()


# Add a community recipe
@login_required(login_url="/recipe/login_page/")
def add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        about = request.POST.get('about')
        img = request.FILES.get('img')

        if name and about and img:
            try:
                img_url = upload_image_to_cloudinary(img, folder="community")
                CommunityRecipe.objects.create(
                    name=name,
                    about=about,
                    img=img_url,
                    created_by=request.user  # Associate recipe with the logged-in user
                )
                return redirect("/recipe/home/")
            except Exception as e:
                messages.error(request, f"Error uploading image: {e}")
                return redirect("/recipe/add/")
        else:
            messages.error(request, "Please enter all required data.")
            return redirect("/recipe/add/")

    recipes = CommunityRecipe.objects.all()
    return render(request, "recipe/add.html", {'recipes': recipes})




# Home page with recipe list and search
@login_required(login_url="/recipe/login_page/")
def home(request):
    recipes = CommunityRecipe.objects.all().order_by('-created_at')
    search_query = request.GET.get('Search', '')

    if search_query:
        recipes = recipes.filter(name__icontains=search_query)
        if not recipes.exists():
            messages.error(request, "Recipe not found.")

    paginator = Paginator(recipes, 3)
    page_number = request.GET.get("page", 1)
    paginated_recipes = paginator.get_page(page_number)

    return render(request, 'recipe/home.html', {
        'recipes': paginated_recipes,
        'search_query': search_query,
    })


# Delete a recipe (community or saved)
@login_required(login_url="/recipe/login_page/")
def delete_recipe(request, id, source):
    if source == "CommunityRecipe":
        recipe = get_object_or_404(CommunityRecipe, id=id, created_by=request.user)  # Check ownership
    elif source == "saved":
        recipe = get_object_or_404(SavedRecipe, id=id)
    else:
        return redirect("/recipe/home/")

    recipe.delete()
    return redirect("/recipe/home/" if source == "CommunityRecipe" else "/recipe/user_pro/")





# Update a community recipe
@login_required(login_url="/recipe/login_page/")
def update_recipe(request, id):
    recipe = get_object_or_404(CommunityRecipe, id=id, created_by=request.user)  # Check ownership

    if request.method == 'POST':
        name = request.POST.get('name')
        about = request.POST.get('about')
        img = request.FILES.get('img')

        if name and about:
            recipe.name = name
            recipe.about = about

            if img:
                # Upload the new image to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    img,
                    folder="community",
                    public_id=f"community/{recipe.id}"
                )
                recipe.img = upload_result.get("secure_url")

            recipe.save()
            messages.success(request, "Recipe updated successfully.")
            return redirect("/recipe/home/")
        else:
            messages.error(request, "All fields are required.")

    return render(request, "recipe/update_recipe.html", {'recipe': recipe})






# User login
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect("/recipe/home/")
        else:
            messages.error(request, "Invalid credentials.")
            return redirect("/recipe/login_page/")

    return render(request, "recipe/login_page.html")


# User signup
def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("/recipe/signup/")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("/recipe/signup/")


        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password
        )
        messages.success(request, "Account created successfully!")
        return redirect("/recipe/login_page/")
    

    return render(request, "recipe/signup.html")


# User logout
def logout_page(request):
    logout(request)
    return redirect('/recipe/login_page/')


# Delete user profile
@login_required(login_url="/recipe/login_page/")
def delete_profile(request):
    if request.method == 'POST':
        request.user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('/recipe/home/')

    return render(request, 'recipe/delete_profile.html')




def explore_recipes(request):
    recipe_name = request.GET.get('Search', '').strip()
    start = int(request.GET.get('start', 0))
    page_size = 3

    recipes, has_more, total_recipes = [], False, 0  # Default values for no search
    next_start, prev_start, last_start = 0, 0, 0
    current_page, total_pages = 1, 1
    show_first_page, show_last_page = False, False

    if recipe_name:
        # Fetch recipes only if there is a search term
        recipes, has_more, total_recipes = fetch_recipes(recipe_name, start, page_size)
        next_start = start + page_size
        prev_start = max(start - page_size, 0)
        last_start = (total_recipes // page_size) * page_size

        current_page = (start // page_size) + 1
        total_pages = (total_recipes // page_size) + (1 if total_recipes % page_size > 0 else 0)
        show_first_page = start > 0
        show_last_page = (start + page_size) < total_recipes

    return render(request, 'recipe/explore_recipes.html', {
        'recipes': recipes,
        'has_more': has_more,
        'recipe_name': recipe_name,
        'next_start': next_start,
        'prev_start': prev_start,
        'last_start': last_start,
        'start': start,
        'total_recipes': total_recipes,
        'current_page': current_page,
        'total_pages': total_pages,
        'show_first_page': show_first_page,
        'show_last_page': show_last_page,
        'search_performed': bool(recipe_name),  # Indicates if a search was performed
    })





# User-specific saved recipes
@login_required(login_url="/recipe/login_page/")
def user_pro(request):
    if request.method == 'POST':
        recipe_label = request.POST.get('recipe_label')
        recipe_url = request.POST.get('recipe_url')
        recipe_image_url = request.POST.get('recipe_image')
        meal_type = request.POST.get('meal_type')
        cuisine_type = request.POST.get('cuisine_type')
        dish_type = request.POST.get('dish_type')
        source = request.POST.get('source')



        try:
            sanitized_label = re.sub(r"[^a-zA-Z0-9_-]", "_", recipe_label)
            folder_path = f"recipes/{request.user.id}"
            img_url = upload_image_to_cloudinary(recipe_image_url, folder=folder_path, public_id=sanitized_label)

            saved_recipe = SavedRecipe.objects.create(
                recipe_label=recipe_label,
                recipe_url=recipe_url,
                recipe_image=img_url,
                meal_type=meal_type,
                cuisine_type=cuisine_type,
                dish_type=dish_type,
                source=source
            )

            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            user_profile.saved_recipes.add(saved_recipe)

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('user_pro')

    user_profile = get_object_or_404(UserProfile, user=request.user)
    saved_recipes = user_profile.saved_recipes.all().order_by('-id')

    # Handle search
    search_query = request.GET.get('Search', '').strip()
    search_performed = bool(search_query)
    if search_performed:
        saved_recipes = saved_recipes.filter(recipe_label__icontains=search_query)

    # Implement pagination
    paginator = Paginator(saved_recipes, 3)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'recipe/user_pro.html', {
        'queryset': page_obj,
        'search_performed': search_performed,
    })