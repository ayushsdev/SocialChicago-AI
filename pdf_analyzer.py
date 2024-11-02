import openai
import json
from typing import Dict
from pathlib import Path
from config import Config
from pdf2image import convert_from_path
import base64  # Add this import
from happyhour_schema import HappyHour



class PDFAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the PDFAnalyzer with OpenAI API key."""
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)

    def extract_images(self, pdf_path: str) -> Dict[int, str]:
        """Extract images from PDF pages and save them to the configured image folder.
        Returns a dictionary mapping page numbers to image file paths."""
        # Create a dictionary to store page number -> image path mapping
        page_images = {}
        
        # Get the PDF filename without extension
        pdf_name = Path(pdf_path).stem
        
        # Create folder for this PDF's images
        pdf_image_dir = Path(Config.IMAGE_FOLDER) / pdf_name
        pdf_image_dir.mkdir(exist_ok=True)
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path)
        
        # Save each page as an image
        for page_num, image in enumerate(images, start=1):
            image_path = pdf_image_dir / f"page_{page_num}.png"
            image.save(str(image_path), "PNG")
            page_images[page_num] = str(image_path)
        
        return page_images
    
    def analyze_images(self, image_paths: Dict[int, str]) -> str:
        """Analyze images using GPT-4V through the OpenAI chat endpoint.
        
        Args:
            image_paths: Dictionary mapping page numbers to image file paths
        
        Returns:
            str: The analysis response from GPT-4V
        """
        # Sort pages by number to maintain order
        sorted_pages = sorted(image_paths.items())
        prompt = """You are a specialized assistant focused on generating structured JSON output for happy hour sessions. Follow these guidelines precisely:

                1. Happy Hour Sessions:
                - Each happy hour session should be represented as an object in an array under the key `"happy_hours"`.
                - Do not add any additional fields or information outside the specified structure.

                2. Structure of Each Happy Hour Session:
                - **Name**:
                    - Extract or infer an appropriate name for each happy hour session.
                    - If no specific name is given, create a descriptive one based on the main features (e.g., `"Monday Happy Hour"` or `"Weekday Evening Special"`).
                    - Keep in mind different happy hour sessions need to have different schedules. If schedules don't exist, just have all the information under one Name in **Deals* 

                - **Schedule**:
                    - **Days**: Use only the exact values: `"Monday"`, `"Tuesday"`, `"Wednesday"`, `"Thursday"`, `"Friday"`, `"Saturday"`, `"Sunday"`. Each day must be capitalized and in a list.
                    - **Times**: Specify the time range in a clear format (e.g., `"3 PM - 6 PM"`). Use standard AM/PM format. Keep in mind that some places have multiple happy hours with different times. Only list the time for the happy hours that lie on the days mentioned in **Days**

                - **Deals**:
                    - Each deal should be a separate object within the `"deals"` array. Make sure the prices are actually deals and not just usual prices marked. Keep an eye out for any kind of crossings or strikethroughs.
                    - Include the following fields for each deal:
                    - **Item**: Name of the food or drink item (e.g., `"Brun-uusto Cheese Sticks"`).
                    - **Description**: Any further details about the food or drink item.
                    - **Deal**: Price or discount details (e.g., `"$13"`, `"50% off"`).
                    - Split compound deals into separate entries (e.g., `"beer and wine half off"` becomes two separate items).

                3. Formatting and Validation Rules:
                - Days must be in the specified format with each day capitalized.
                - Times should follow a consistent AM/PM format.
                - Each happy hour session must contain `name`, `schedule`, and `deals` fields.
                - Only include deals that are explicitly stated as specials or discounted items.

                4. Constraints:
                - All data should be encapsulated within a JSON object with a single key, `"happy_hours"`, containing an array of happy hour sessions.
                - Ensure that only the specified fields are present; no additional properties should be included.
                - The JSON output should be valid and well-formatted. Do not include any explanations, notes, or additional text.

                If any required information is missing:
                - For **days**: Include only explicitly mentioned days.
                - For **times**: If no time is specified, do not add a placeholder or make assumptions.
                - For **deals**: Only include clearly described deals.
                    """
        
        # Prepare messages with images
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text", 
                        "text": prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Here are the images to analyze:"
                    }
                ]
            }
        ]
        
        # Add each image to the message content
        for page_num, image_path in sorted_pages:
            print(f"Adding image for page {page_num}")
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{self.encode_image(image_path)}"
                }
            })
        
        # Call the OpenAI Chat API with GPT-4V
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=messages,
                response_format=HappyHour
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error analyzing images with GPT-4V: {str(e)}")
        
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')