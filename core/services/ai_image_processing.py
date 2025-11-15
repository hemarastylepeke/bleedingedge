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
    Extract text from image using OpenAI's Vision API with enhanced prompt
    """
    try:
        # Read and encode the image
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Enhanced prompt for comprehensive information extraction
        prompt = """
        Analyze this product image and extract ALL available information. Look for:
        
        1. PRODUCT NAME: The main product name/title
        2. EXPIRY/BEST BEFORE DATE: Any date information (dd/mm/yyyy, mm/dd/yyyy, etc.)
        3. NUTRITIONAL INFORMATION: Calories, protein, carbs, fat, fiber per 100g
        4. BARCODE/UPC: Any barcode numbers
        5. WEIGHT/VOLUME: Quantity and unit (g, kg, ml, l, etc.)
        6. BRAND/MANUFACTURER: Brand name if visible
        7. STORAGE INSTRUCTIONS: Any storage guidance
        
        Return the information in this exact JSON format:
        {
            "product_name": "extracted product name or null",
            "expiry_date": "YYYY-MM-DD or null",
            "barcode": "barcode number or null",
            "quantity": number or null,
            "unit": "g/ml/kg/l etc or null",
            "calories": number or null,
            "protein": number or null,
            "carbs": number or null,
            "fat": number or null,
            "fiber": number or null,
            "brand": "brand name or null",
            "storage_instructions": "storage info or null",
            "detected_text": "all raw text found in image"
        }
        
        Only return valid JSON, no other text.
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
            max_tokens=1500,
        )
        
        extracted_text = response.choices[0].message.content.strip()
        logger.info(f"Raw AI response: {extracted_text}")
        
        # Parse JSON response
        try:
            import json
            extracted_data = json.loads(extracted_text)
            return extracted_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            # Fallback to text extraction
            return {"detected_text": extracted_text}
        
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

def extract_quantity_and_unit(text):
    """
    Extract quantity and unit from text
    """
    if not text:
        return None, None
    
    # Common quantity patterns
    patterns = [
        r'(\d+\.?\d*)\s*(g|kg|ml|l|mg|oz|lb)\b',
        r'(\d+\.?\d*)\s*(gram|kilogram|milliliter|liter|pound|ounce)s?\b',
        r'\b(\d+)\s*(pieces|pcs|items|units)\b',
        r'net\s+weight\s*:\s*(\d+\.?\d*)\s*(g|kg|ml|l)\b',
        r'(\d+\.?\d*)\s*(g|kg|ml|l)\s*\/',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            quantity = float(match[0])
            unit = match[1]
            
            # Normalize units
            unit_map = {
                'gram': 'g', 'grams': 'g', 'kilogram': 'kg', 'kilograms': 'kg',
                'milliliter': 'ml', 'milliliters': 'ml', 'liter': 'l', 'liters': 'l',
                'ounce': 'oz', 'ounces': 'oz', 'pound': 'lb', 'pounds': 'lb',
                'piece': 'pieces', 'pcs': 'pieces', 'items': 'pieces', 'units': 'pieces'
            }
            unit = unit_map.get(unit, unit)
            
            return quantity, unit
    
    return None, None

def extract_nutritional_info(text):
    """
    Extract nutritional information from text
    """
    if not text:
        return {}
    
    nutritional_info = {}
    
    # Calories patterns
    calorie_patterns = [
        r'calories?[:\s]*(\d+\.?\d*)\s*(?:kcal)?',
        r'energy[:\s]*(\d+\.?\d*)\s*(?:kcal|kj)',
        r'(\d+\.?\d*)\s*kcal\s*per\s*100g',
    ]
    
    for pattern in calorie_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            if isinstance(match, tuple):
                nutritional_info['calories'] = float(match[0])
            else:
                nutritional_info['calories'] = float(match)
            break
    
    # Protein patterns
    protein_patterns = [
        r'protein[:\s]*(\d+\.?\d*)\s*g',
        r'(\d+\.?\d*)\s*g\s*protein\s*per\s*100g',
    ]
    
    for pattern in protein_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            nutritional_info['protein'] = float(match)
            break
    
    # Carbs patterns
    carbs_patterns = [
        r'carbohydrates?[:\s]*(\d+\.?\d*)\s*g',
        r'carbs[:\s]*(\d+\.?\d*)\s*g',
        r'(\d+\.?\d*)\s*g\s*carbohydrates?\s*per\s*100g',
    ]
    
    for pattern in carbs_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            nutritional_info['carbs'] = float(match)
            break
    
    # Fat patterns
    fat_patterns = [
        r'fat[:\s]*(\d+\.?\d*)\s*g',
        r'(\d+\.?\d*)\s*g\s*fat\s*per\s*100g',
    ]
    
    for pattern in fat_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            nutritional_info['fat'] = float(match)
            break
    
    # Fiber patterns
    fiber_patterns = [
        r'fiber[:\s]*(\d+\.?\d*)\s*g',
        r'fibre[:\s]*(\d+\.?\d*)\s*g',
        r'dietary\s+fiber[:\s]*(\d+\.?\d*)\s*g',
    ]
    
    for pattern in fiber_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            nutritional_info['fiber'] = float(match)
            break
    
    return nutritional_info

def extract_product_info_from_text(text):
    """
    Extract comprehensive product information from text
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
                not line.lower().startswith(('exp', 'best', 'use', 'bb', 'mf', 'ingredients', 'nutrition'))):
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
    
    # Extract quantity and unit
    quantity, unit = extract_quantity_and_unit(text)
    if quantity:
        info['quantity'] = quantity
    if unit:
        info['unit'] = unit
    
    # Extract nutritional information
    nutritional_info = extract_nutritional_info(text)
    info.update(nutritional_info)
    
    # Extract storage instructions
    storage_patterns = [
        r'store[:\s]*([^.]+\.)',
        r'storage[:\s]*([^.]+\.)',
        r'keep[:\s]*([^.]+\.)',
    ]
    
    for pattern in storage_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            info['storage_instructions'] = match.strip()
            break
    
    return info

def process_pantry_item_images(product_image=None, expiry_label_image=None, current_data=None):
    """
    Main function to process uploaded images and extract comprehensive information
    Returns updated data dictionary
    """
    extracted_data = current_data or {}
    
    try:
        # Process expiry label image first (highest priority for dates)
        if expiry_label_image:
            logger.info("Processing expiry label image...")
            ai_data = extract_text_from_image(expiry_label_image)
            if ai_data:
                # Extract expiry date
                if ai_data.get('expiry_date'):
                    extracted_data['expiry_date'] = ai_data['expiry_date']
                elif ai_data.get('detected_text'):
                    expiry_date = parse_expiry_date_from_text(ai_data['detected_text'])
                    if expiry_date:
                        extracted_data['expiry_date'] = expiry_date
                
                # Extract other information from expiry label
                if ai_data.get('detected_text'):
                    product_info = extract_product_info_from_text(ai_data['detected_text'])
                    extracted_data.update(product_info)
        
        # Process product image (secondary source of information)
        if product_image:
            logger.info("Processing product image...")
            ai_data = extract_text_from_image(product_image)
            if ai_data:
                # Only extract expiry date if not already found
                if 'expiry_date' not in extracted_data:
                    if ai_data.get('expiry_date'):
                        extracted_data['expiry_date'] = ai_data['expiry_date']
                    elif ai_data.get('detected_text'):
                        expiry_date = parse_expiry_date_from_text(ai_data['detected_text'])
                        if expiry_date:
                            extracted_data['expiry_date'] = expiry_date
                
                # Extract comprehensive product information
                if ai_data.get('product_name') and ai_data['product_name'] != 'null':
                    extracted_data['product_name'] = ai_data['product_name']
                
                if ai_data.get('barcode') and ai_data['barcode'] != 'null':
                    extracted_data['barcode'] = ai_data['barcode']
                
                if ai_data.get('quantity') and ai_data['quantity'] != 'null':
                    extracted_data['quantity'] = ai_data['quantity']
                
                if ai_data.get('unit') and ai_data['unit'] != 'null':
                    extracted_data['unit'] = ai_data['unit']
                
                # Extract nutritional information from AI response
                nutritional_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber']
                for field in nutritional_fields:
                    if ai_data.get(field) and ai_data[field] != 'null':
                        extracted_data[field] = ai_data[field]
                
                if ai_data.get('storage_instructions') and ai_data['storage_instructions'] != 'null':
                    extracted_data['storage_instructions'] = ai_data['storage_instructions']
                
                # Fallback to text extraction if AI JSON parsing failed
                if ai_data.get('detected_text'):
                    product_info = extract_product_info_from_text(ai_data['detected_text'])
                    # Only update fields that weren't already set by AI JSON
                    for key, value in product_info.items():
                        if key not in extracted_data or not extracted_data[key]:
                            extracted_data[key] = value
        
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
        
        # Update nutritional information if available
        nutritional_fields = ['calories', 'protein', 'carbs', 'fat', 'fiber']
        for field in nutritional_fields:
            if extracted_data.get(field) and getattr(pantry_item_instance, field) == 0:
                setattr(pantry_item_instance, field, extracted_data[field])
                updated = True
        
        if extracted_data.get('quantity') and pantry_item_instance.quantity == 1.0:
            pantry_item_instance.quantity = extracted_data['quantity']
            updated = True
        
        if extracted_data.get('unit') and not pantry_item_instance.unit:
            pantry_item_instance.unit = extracted_data['unit']
            updated = True
        
        if extracted_data.get('storage_instructions') and not pantry_item_instance.storage_instructions:
            pantry_item_instance.storage_instructions = extracted_data['storage_instructions']
            updated = True
        
        if updated:
            pantry_item_instance.save()
            logger.info(f"Enhanced pantry item {pantry_item_instance.id} with AI data")
            
            return True
            
    except Exception as e:
        logger.error(f"Error enhancing pantry item with AI: {str(e)}")
    
    return False