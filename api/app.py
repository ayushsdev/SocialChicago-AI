import os

# Handle imports differently for local vs Vercel environment
from api.config import Config
from api.utils import allowed_file, is_directory_empty
from api.pdf_analyzer import PDFAnalyzer


from flask import Flask, request, jsonify
from flask_cors import CORS  # Add this import
from datetime import datetime
from dotenv import load_dotenv
import json
import tempfile
import shutil

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config.from_object(Config)

# Initialize the PDFAnalyzer with environment variable
analyzer = PDFAnalyzer(os.getenv('OPENAI_API_KEY'))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload a PDF file, extract images, and analyze them."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400

    try:
        # Ensure directories exist
        Config.ensure_directories()
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save the file
        file.save(filepath)
        
        try:
            # Extract images from the PDF
            page_images = analyzer.extract_images(filepath)
            
            # Analyze the extracted images
            analysis_result = analyzer.analyze_images(page_images)
            
            return jsonify({
                'message': 'File uploaded, images extracted and analyzed successfully',
                'filename': filename,
                'analysis': analysis_result
            }), 200
            
        finally:
            # Clean up files in a finally block to ensure they're removed
            try:
                # Delete the uploaded PDF file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # Delete all images in the PDF's specific folder
                pdf_name = os.path.splitext(filename)[0]
                pdf_image_dir = os.path.join(Config.IMAGE_FOLDER, pdf_name)
                if os.path.exists(pdf_image_dir):
                    for image_file in os.listdir(pdf_image_dir):
                        image_path = os.path.join(pdf_image_dir, image_file)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    os.rmdir(pdf_image_dir)
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
                
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


if __name__ == '__main__':
    app.run()
