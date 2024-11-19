import requests,re


from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

# Now you can use os.getenv() to get your environment variables
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")



def fetch_recipes(recipe_name, start=0, page_size=3):
    api_url = "https://api.edamam.com/search"
    params = {
        'q': recipe_name,
        'app_id': APP_ID,
        'app_key': APP_KEY,
        'from': start,
        'to': start + page_size
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        recipes = data.get('hits', [])
        total_recipes = data.get('count', 0)  # Total available recipes from the API
        has_more = (start + page_size) < total_recipes
    else:
        print("Error fetching recipes:", response.status_code)
        recipes, has_more, total_recipes = [], False, 0

    return recipes, has_more, total_recipes


def clean_filename(filename):
    if not filename:
        raise ValueError("Filename is required to clean it.")
    return re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')



import cloudinary.uploader
def upload_image_to_cloudinary(image, folder="general", public_id=None):
    """
    Uploads an image to Cloudinary.

    Args:
        image (File or str): The image file or URL to upload.
        folder (str): The folder in Cloudinary where the image will be stored.
        public_id (str): Optional public ID for the image.

    Returns:
        str: Secure URL of the uploaded image.
    """
    try:
        # Prepare upload options
        upload_options = {
            "folder": folder,
            "overwrite": True,
        }
        if public_id:
            upload_options["public_id"] = public_id

        # Check if the image is a URL or a file
        if isinstance(image, str) and (image.startswith('http://') or image.startswith('https://')):
            upload_result = cloudinary.uploader.upload(image, **upload_options)
        else:
            upload_result = cloudinary.uploader.upload(image, **upload_options)

        return upload_result.get("secure_url")
    except Exception as e:
        raise ValueError(f"Error uploading image to Cloudinary: {str(e)}")
    
