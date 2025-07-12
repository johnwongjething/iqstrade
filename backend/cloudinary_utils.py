import os
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

def upload_filelike_to_cloudinary(file, folder="uploads"):
    """
    Uploads a file-like object (e.g. from Flask request.files) to Cloudinary.
    Returns the secure_url.
    """
    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="auto",
    )
    return result.get("secure_url")


def upload_filepath_to_cloudinary(file_path, folder="invoices"):
    """
    Uploads a PDF file saved on disk (e.g. generated invoice) to Cloudinary.
    Returns the secure_url.
    """
    result = cloudinary.uploader.upload(
        file_path,
        folder=folder,
        resource_type="auto",
    )
    return result.get("secure_url")
