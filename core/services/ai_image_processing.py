import openai
import base64
import io
from PIL import Image
import re
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def extract_text_from_image(image_file):
    """
    Extract text from image using OpenAI's Vision API
    """
    try:
        # Read and encode the image
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Prepare the prompt for text extraction
        prompt = """
        Extract ALL visible text from this image. Return ONLY the raw text exactly as it appears, 
        without any interpretation, formatting, or additional comments. 
        Preserve line breaks and spacing exactly as they appear.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        
        extracted_text = response.choices[0].message.content.strip()
        logger.info(f"Extracted text from image: {extracted_text}")
        return extracted_text
        
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return None

def parse_expiry_date_from_text(text):
    """
    Parse expiry date from extracted text using multiple pattern matching
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Common expiry date patterns
    patterns = [
        # "Expiry: 2024-12-31", "Best before: 31/12/2024"
        r'(?:expiry|exp|best before|use by|use before|best by)[:\s]*([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{2,4})',
        r'(?:expiry|exp|best before|use by|use before|best by)[:\s]*([a-zA-Z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})',
        r'(?:expiry|exp|best before|use by|use before|best by)[:\s]*([0-9]{1,2}\s+[a-zA-Z]{3,9}\s+[0-9]{4})',
        
        # Direct date patterns
        r'\b([0-9]{1,2}[/\-\.][0-9]{1,2}[/\-\.][0-9]{2,4})\b',
        r'\b([a-zA-Z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})\b',
        r'\b([0-9]{1,2}\s+[a-zA-Z]{3,9}\s+[0-9]{4})\b',
        
        # Month-year patterns
        r'\b([a-zA-Z]{3,9}\s+[0-9]{4})\b',
        r'\b([0-9]{1,2}/[0-9]{4})\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            date_str = match.strip()
            parsed_date = try_parse_date(date_str)
            if parsed_date:
                logger.info(f"Found expiry date: {parsed_date} from text: '{date_str}'")
                return parsed_date
    
    return None

def try_parse_date(date_str):
    """
    Try to parse date string in multiple formats
    """
    date_formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
        '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
        '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',
        '%m/%d/%y', '%m-%d-%y', '%m.%d.%y',
        '%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d',
        '%B %d, %Y', '%b %d, %Y',
        '%d %B %Y', '%d %b %Y',
        '%B %Y', '%b %Y', '%m/%Y'
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # Validate that the date is reasonable (not too far in the past or future)
            current_year = timezone.now().year
            if 2020 <= parsed_date.year <= current_year + 5:
                return parsed_date
        except ValueError:
            continue
    
    return None

def extract_product_info_from_text(text):
    """
    Extract product name and other information from text
    """
    if not text:
        return {}
    
    info = {}
    lines = text.split('\n')
    
    # Look for product name (usually first non-empty line or line with common product indicators)
    for line in lines:
        line = line.strip()
        if line and len(line) > 2:
            # Skip lines that are likely dates, numbers, or short codes
            if (not re.search(r'\d{2,}', line) and 
                len(line) > 10 and 
                not line.lower().startswith(('exp', 'best', 'use', 'bb', 'mf'))):
                info['product_name'] = line
                break
    
    # Look for barcode
    barcode_patterns = [
        r'\b\d{8,13}\b',  # 8-13 digit barcodes
        r'[A-Z0-9]{10,15}',  # Alphanumeric codes
    ]
    
    for pattern in barcode_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) >= 8:  # Reasonable barcode length
                info['barcode'] = match
                break
    
    return info

def process_pantry_item_images(product_image=None, expiry_label_image=None, current_data=None):
    """
    Main function to process uploaded images and extract information
    Returns updated data dictionary
    """
    extracted_data = current_data or {}
    
    try:
        # Process expiry label image first (highest priority for dates)
        if expiry_label_image:
            logger.info("Processing expiry label image...")
            expiry_text = extract_text_from_image(expiry_label_image)
            if expiry_text:
                expiry_date = parse_expiry_date_from_text(expiry_text)
                if expiry_date:
                    extracted_data['expiry_date'] = expiry_date
                    logger.info(f"Extracted expiry date: {expiry_date}")
                
                # Also extract product info from expiry label
                product_info = extract_product_info_from_text(expiry_text)
                extracted_data.update(product_info)
        
        # Process product image (secondary source of information)
        if product_image and ('expiry_date' not in extracted_data or 'product_name' not in extracted_data):
            logger.info("Processing product image...")
            product_text = extract_text_from_image(product_image)
            if product_text:
                # Only extract expiry date if not already found
                if 'expiry_date' not in extracted_data:
                    expiry_date = parse_expiry_date_from_text(product_text)
                    if expiry_date:
                        extracted_data['expiry_date'] = expiry_date
                        logger.info(f"Extracted expiry date from product image: {expiry_date}")
                
                # Extract product info
                product_info = extract_product_info_from_text(product_text)
                extracted_data.update(product_info)
        
        # Log what was extracted
        if extracted_data:
            logger.info(f"AI extracted data: {extracted_data}")
        else:
            logger.info("No data extracted from images")
            
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
    
    return extracted_data

def enhance_pantry_item_with_ai(pantry_item_instance):
    """
    Enhance an existing pantry item with AI-extracted data from its images
    """
    try:
        extracted_data = {}
        
        # Process existing images
        if pantry_item_instance.expiry_label_image:
            extracted_data.update(
                process_pantry_item_images(
                    expiry_label_image=pantry_item_instance.expiry_label_image
                )
            )
        
        if pantry_item_instance.product_image and not extracted_data.get('expiry_date'):
            extracted_data.update(
                process_pantry_item_images(
                    product_image=pantry_item_instance.product_image
                )
            )
        
        # Update the instance with extracted data
        updated = False
        if extracted_data.get('expiry_date') and not pantry_item_instance.expiry_date:
            pantry_item_instance.expiry_date = extracted_data['expiry_date']
            updated = True
        
        if extracted_data.get('product_name') and not pantry_item_instance.name:
            pantry_item_instance.name = extracted_data['product_name']
            updated = True
        
        if extracted_data.get('barcode') and not pantry_item_instance.barcode:
            pantry_item_instance.barcode = extracted_data['barcode']
            updated = True
        
        if updated:
            pantry_item_instance.save()
            logger.info(f"Enhanced pantry item {pantry_item_instance.id} with AI data")
            return True
            
    except Exception as e:
        logger.error(f"Error enhancing pantry item with AI: {str(e)}")
    
    return False