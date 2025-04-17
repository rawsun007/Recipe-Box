import requests,re


from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env

# Now you can use os.getenv() to get your environment variables
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")



def fetch_recipes(recipe_name, start=0):
    api_url = "https://api.edamam.com/api/recipes/v2"
    params = {
        'type': 'public',
        'q': recipe_name,
        'app_id': APP_ID,
        'app_key': APP_KEY,
        # Request a full page of results (up to 20)
        'from': start,
        'to': start + 20
    }
    
    headers = {
        'accept': 'application/json',
        'Edamam-Account-User': APP_ID,
        'Accept-Language': 'en'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        

        if 'hits' in data:
            all_recipes = data.get('hits', [])
            total_recipes = data.get('count', 0)
            has_more = len(all_recipes) < total_recipes
            return all_recipes, has_more, total_recipes
        else:
            print("Error: No hits in response")
            return [], False, 0

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return [], False, 0
    
    
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
    
