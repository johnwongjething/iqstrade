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
    # Always upload PDFs as resource_type='raw' for direct access
    filename = getattr(file_obj, 'filename', None)
    ext = ''
    public_id = None
    if filename:
        ext = os.path.splitext(filename)[1]
        # Remove . from extension
        ext = ext if ext.startswith('.') else f'.{ext}'
        # Generate a random public_id (like before) but always end with .pdf for PDFs
        import uuid
        base_id = str(uuid.uuid4()).replace('-', '')[:20]
        if ext.lower() == '.pdf':
            public_id = f"{folder}/{base_id}.pdf"
        else:
            public_id = f"{folder}/{base_id}{ext}"
    else:
        # fallback: just use folder and random id
        import uuid
        base_id = str(uuid.uuid4()).replace('-', '')[:20]
        public_id = f"{folder}/{base_id}"
    result = cloudinary.uploader.upload(file_obj, folder=None, public_id=public_id, resource_type='raw')
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
