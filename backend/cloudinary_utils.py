import cloudinary
import cloudinary.uploader
import os

# Configure Cloudinary (replace with your credentials)
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'your_cloud_name'),
    api_key=os.getenv('CLOUDINARY_API_KEY', 'your_api_key'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'your_api_secret'),
    secure=True
)

def upload_filelike_to_cloudinary(file_obj, folder=None):
    """
    Uploads a file-like object to Cloudinary and returns the secure_url.
    """
    print(f"[DEBUG] cloudinary_utils: Uploading file to Cloudinary, folder={folder}")
    result = cloudinary.uploader.upload(file_obj, folder=folder)
    print(f"[DEBUG] cloudinary_utils: Cloudinary upload result: {result}")
    return result.get('secure_url')

def upload_filepath_to_cloudinary(filepath, folder=None):
    """
    Uploads a file from disk to Cloudinary and returns the secure_url.
    """
    print(f"[DEBUG] cloudinary_utils: Uploading file from path to Cloudinary: {filepath}, folder={folder}")
    result = cloudinary.uploader.upload(filepath, folder=folder)
    print(f"[DEBUG] cloudinary_utils: Cloudinary upload result: {result}")
    return result.get('secure_url')
