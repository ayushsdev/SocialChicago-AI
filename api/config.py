import os

class Config:
    UPLOAD_FOLDER = 'uploads'
    IMAGE_FOLDER = 'extracted_images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.IMAGE_FOLDER, exist_ok=True)
