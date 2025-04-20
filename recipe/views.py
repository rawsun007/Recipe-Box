# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import CommunityRecipe, SavedRecipe, UserProfile
from .utils import upload_image_to_cloudinary, fetch_recipes
import re  # For sanitizing public IDs
import requests
import cloudinary
import cloudinary.uploader
from django.contrib.auth import get_user_model
User = get_user_model()


def custom_404(request, exception):
    return render(request, '404.html', status=404)


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

    # Check for AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        template = 'recipe/home_partial.html'
    else:
        template = 'recipe/home.html'

    return render(request, template, {
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
            return redirect("/recipe/explore_recipes/")
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
    api_start = int(request.GET.get('api_start', 0))
    page = int(request.GET.get('page', 1))
    page_size = 3

    # Calculate client-side paging
    recipes_buffer = request.session.get('recipes_buffer', [])
    total_recipes = request.session.get('total_recipes', 0)
    current_search = request.session.get('current_search', '')

    # If new search or no buffer, fetch from API
    if recipe_name and (recipe_name != current_search or not recipes_buffer):
        all_recipes, has_more, total_count = fetch_recipes(recipe_name, 0)
        request.session['recipes_buffer'] = all_recipes
        request.session['current_search'] = recipe_name
        request.session['total_recipes'] = total_count
        recipes_buffer = all_recipes
        total_recipes = total_count
        api_start = 0

    # Calculate indices for current page
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    # If user paginates past current buffer, fetch more from API and append
    while recipe_name and end_idx > len(recipes_buffer) and len(recipes_buffer) < total_recipes:
        # Fetch next batch from API
        next_api_start = len(recipes_buffer)
        new_recipes, has_more, _ = fetch_recipes(recipe_name, next_api_start)
        if not new_recipes:
            break  # No more recipes to fetch
        recipes_buffer += new_recipes
        request.session['recipes_buffer'] = recipes_buffer  # Update session buffer

    # Now get the current page's recipes
    current_page_recipes = recipes_buffer[start_idx:end_idx] if recipes_buffer else []

    # Calculate if we need more data from API for next page
    need_more_data = len(recipes_buffer) <= end_idx and total_recipes > len(recipes_buffer)

    # Calculate pagination controls
    total_pages = (total_recipes // page_size) + (1 if total_recipes % page_size > 0 else 0)
    has_next = page < total_pages
    has_prev = page > 1
    next_page = page + 1 if has_next else page
    prev_page = page - 1 if has_prev else page

    # Calculate API pagination
    next_api_start = len(recipes_buffer) if need_more_data else api_start

    # Determine template based on AJAX request
    template = 'recipe/explore_recipes.html'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        template = 'recipe/recipe_results.html'

    return render(request, template, {
        'recipes': current_page_recipes,
        'recipe_name': recipe_name,
        'page': page,
        'next_page': next_page,
        'prev_page': prev_page,
        'has_next': has_next,
        'has_prev': has_prev,
        'total_pages': total_pages,
        'total_recipes': total_recipes,
        'api_start': api_start,
        'next_api_start': next_api_start,
        'need_more_data': need_more_data,
        'search_performed': bool(recipe_name),
    })


# User-specific saved recipes
@login_required(login_url="/recipe/login_page/")
def save_user_recipe(request):
    if request.method == 'POST':
        recipe_label = request.POST.get('recipe_label')
        recipe_url = request.POST.get('recipe_url')
        recipe_image_url = request.POST.get('recipe_image')
        meal_type = request.POST.get('meal_type')
        cuisine_type = request.POST.get('cuisine_type')
        dish_type = request.POST.get('dish_type')
        source = request.POST.get('source')

        # Validate input data
        if not all([recipe_label, recipe_url, recipe_image_url]):
            messages.error(request, "Invalid recipe data. Please try again.")
            return redirect('user_pro')

        try:
            # Sanitize the label for cloud storage
            sanitized_label = re.sub(r"[^a-zA-Z0-9_-]", "_", recipe_label)
            folder_path = f"recipes/{request.user.id}"
            img_url = upload_image_to_cloudinary(recipe_image_url, folder=folder_path, public_id=sanitized_label)

            # Save the recipe
            saved_recipe = SavedRecipe.objects.create(
                recipe_label=recipe_label,
                recipe_url=recipe_url,
                recipe_image=img_url,
                meal_type=meal_type,
                cuisine_type=cuisine_type,
                dish_type=dish_type,
                source=source
            )

            # Associate with the user's profile
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            user_profile.saved_recipes.add(saved_recipe)

            messages.success(request, f"Recipe '{recipe_label}' saved successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('user_pro')

        # Redirect to the user profile after saving
        return redirect('user_pro')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('user_pro')


@login_required(login_url="/recipe/login_page/")
def user_pro(request):
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
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)  # Default to the first page

    # Render partial if AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'recipe/user_pro_cards_partial.html', {
            'queryset': page_obj,
            'search_performed': search_performed,
            'search_query': search_query,
        })
    return render(request, 'recipe/user_pro.html', {
        'queryset': page_obj,
        'search_performed': search_performed,
        'search_query': search_query,
    })