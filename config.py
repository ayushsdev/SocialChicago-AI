import os

class Config:
    UPLOAD_FOLDER = 'uploads'
    IMAGE_FOLDER = 'extracted_images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}

# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.IMAGE_FOLDER, exist_ok=True)
