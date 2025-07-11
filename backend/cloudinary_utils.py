import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

def upload_to_cloudinary(file, folder=None):
    options = {"resource_type": "auto"}
    if folder:
        options["folder"] = folder
    result = cloudinary.uploader.upload(file, **options)
    return result.get("secure_url")
