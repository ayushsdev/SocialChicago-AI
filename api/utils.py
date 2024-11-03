from config import Config
import os

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def is_directory_empty(directory):
    """Check if a directory is empty."""
    return len(os.listdir(directory)) == 0
