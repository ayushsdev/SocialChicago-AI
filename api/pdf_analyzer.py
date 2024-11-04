import openai
import json
from typing import Dict
from pathlib import Path
import base64
import os
from pdf2image import convert_from_path


# Handle imports differently for local vs Vercel environment
from api.config import Config
from api.happyhour_schema import HappyHour




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
        
        # Create temporary folder for this PDF's images
        pdf_image_dir = Path(Config.IMAGE_FOLDER) / pdf_name
        pdf_image_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        prompt = """You are a specialized assistant focused on generating structured JSON output for happy hour sessions. Analyze the entire image carefully, including edges and corners, to ensure no information is missed.

                1. Image Analysis Guidelines:
                    - Examine all edges and corners of each image thoroughly
                    - Look for text that might be partially cut off or faded
                    - Pay attention to footnotes, headers, and margins
                    - If text appears to continue beyond the image boundary, note this in the description
                    - Cross-reference information between multiple pages when available

                2. Happy Hour Sessions Structure:
                    - Each distinct happy hour session (different times/days) must be a separate object in the "happy_hours" array
                    - Multiple deals with the same schedule should be grouped under one session
                    - Validate that each session has unique scheduling

                3. Required Fields for Each Session:
                    a) "name" (string):
                        - Must be unique and descriptive
                        - Examples: "Weekend Afternoon Special", "Weekday Evening Happy Hour"
                        - Include timing in name if multiple sessions exist

                    b) "schedule" (object):
                        - "days": [Strict format: "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        - "start_time": 24-hour format (HH:MM)
                        - "end_time": 24-hour format (HH:MM)
                        - All times must be exact, no assumptions
                        - Do not hallucinate start and end times. Keep them empty if not sure.
                        - If any kind of days or time is not mentioned, keep those fields empty.

                    c) "deals" (array of objects):
                        Each deal must include:
                        - "item": Specific item name
                        - "description": Detailed description including size, restrictions, exclusions
                        - "deal": Exact price or discount. If it's a percentage, put it in percentage form. If it's a dollar amount, put it in dollar amount form. If there are just numbers, its most likely a dollar amount.
                        - Split combination deals into individual items
                        - Verify prices are actually discounted (look for strike-throughs, "regular price" mentions)

                    d) "deals_summary" (string):
                        - Maximum 250 characters
                        - Highlight best value deals
                        - Include price ranges
                        - Mention any notable restrictions

                4. Data Quality Rules:
                    - No missing required fields
                    - No placeholder data
                    - No assumed information
                    - Validate all prices and times
                    - Confirm deals are actual discounts, not regular prices
                    - Note any seasonal or temporary specifications

                5. Output Format:
                    {
                        "happy_hours": [
                            {
                                "name": string,
                                "schedule": {
                                    "days": string[],
                                    "start_time": string,
                                    "end_time": string
                                },
                                "deals": [
                                    {
                                        "item": string,
                                        "description": string,
                                        "deal": string
                                    }
                                ],
                                "deals_summary": string
                            }
                        ]
                    }

                6. Special Instructions:
                    - If information spans multiple pages, cross-reference to ensure accuracy
                    - Include any seasonal variations or special conditions in descriptions
                    - Note any restrictions or exclusions clearly
                    - If deal validity dates are mentioned, include in description
                    - Flag any ambiguous or unclear information in descriptions
                    - Ensure all prices are current and marked as specials/discounts

                Remember: Accuracy over completeness. If information is unclear or ambiguous, exclude it rather than make assumptions."""
                        
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