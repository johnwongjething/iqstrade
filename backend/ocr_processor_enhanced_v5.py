#!/usr/bin/env python3
"""
Enhanced OCR Processor V5 - Re-validation System
Adds intelligent re-validation when required fields are missing
Uses multiple extraction strategies and enhanced prompts
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from ocr_processor import call_openai_vision_fallback

def openai_call_with_fallback_old_api(messages, temperature=0, max_tokens=None):
    """
    Make OpenAI API call with fallback from GPT-3.5-turbo to GPT-4o using old API format
    """
    import openai
    
    # Check if the message contains image content
    has_image = False
    for message in messages:
        if isinstance(message.get('content'), list):
            for content_item in message['content']:
                if content_item.get('type') == 'image_url':
                    has_image = True
                    break
        if has_image:
            break
    
    # Use vision-capable models if image is present
    if has_image:
        models = ["gpt-4o", "gpt-4o-mini"]
    else:
        models = ["gpt-3.5-turbo", "gpt-4o"]
    
    for i, model in enumerate(models):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            response = openai.ChatCompletion.create(**kwargs)
            content = response.choices[0].message.content
            return content
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "billing" in error_msg:
                if i < len(models) - 1:
                    continue
                else:
                    raise e
            else:
                raise e
    
    raise Exception("All OpenAI models failed")
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))
import openai
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

@dataclass
class ContainerInfo:
    """Container information extracted from document"""
    container_numbers: List[str]
    container_types: List[str]  # ['20ft', '40ft', '40ft_hc']
    container_count: int
    confidence: float

@dataclass
class WeightInfo:
    """Weight information extracted from document"""
    total_weight_kg: Optional[float]
    weight_unit: str  # 'kg' or 'lbs'
    confidence: float

@dataclass
class ShipmentInfo:
    """Shipment type classification"""
    shipment_type: str  # 'ocean', 'air', 'loose_cargo'
    confidence: float

@dataclass
class ValidationResult:
    """Result of field validation"""
    missing_fields: List[str]
    has_critical_missing: bool
    confidence_score: float
    needs_revalidation: bool

class EnhancedAIOCRProcessorV5:
    """Enhanced AI-based OCR processor V5 - Re-validation system"""
    
    def __init__(self):
        # Required fields for different document types
        self.required_fields = {
            'BOL': ['shipper', 'consignee', 'port_of_loading', 'port_of_discharge', 'bl_number'],
            'AWB': ['shipper', 'consignee', 'port_of_loading', 'port_of_discharge', 'bl_number', 'flight_or_vessel']
        }
        
        # Critical fields that must be present
        self.critical_fields = ['shipper', 'consignee', 'bl_number']
        
        # Container type patterns for post-processing
        self.container_patterns = {
            '20ft': [
                r'\b20\s*ft\b',
                r'\b20\s*feet\b',
                r'\b20\'\b',
                r'\b20\s*foot\b',
                r'\b20ST\b',
                r'\b20\s*ST\b'
            ],
            '40ft': [
                r'\b40\s*ft\b',
                r'\b40\s*feet\b',
                r'\b40\'\b',
                r'\b40\s*foot\b'
            ],
            '40ft_hc': [
                r'\b40\s*ft\s*hc\b',
                r'\b40\s*feet\s*hc\b',
                r'\b40\s*ft\s*high\s*cube\b',
                r'\b40\s*feet\s*high\s*cube\b',
                r'\b40\s*ft\s*high\s*container\b',
                r'\b40\s*[\'`]\s*hq\b',
                r'\b40\s*[\'`]\s*hc\b',
                r'\b2\s*[Xx]\s*40\s*[\'`]\s*hq\b',
                r'\b2\s*[Xx]\s*40\s*[\'`]\s*hc\b',
                r'\b40\s*HIGH\s*CUBE\b',
                r'\b40\s*HQ\b'
            ]
        }
        
        # Enhanced patterns for missing field extraction
        self.enhanced_patterns = {
            'shipper': [
                r'\b(?:shipper|exporter|consignor)[:\s]*([^\n\r,]+)',
                r'\b(?:from|sender)[:\s]*([^\n\r,]+)',
                r'\b(?:company|business)[:\s]*([^\n\r,]+)',
                r'\b([A-Z][A-Z\s&.,]+(?:INC|LTD|LLC|CORP|CO|COMPANY|GROUP))',
                r'\b([A-Z][A-Z\s&.,]+(?:INTERNATIONAL|INTL|GLOBAL|WORLD))'
            ],
            'consignee': [
                r'\b(?:consignee|consigned\s+to|consignee\s+name)[:\s]*([^\n\r,]+)',
                r'\b(?:to|recipient|buyer)[:\s]*([^\n\r,]+)',
                r'\b(?:deliver\s+to|ship\s+to)[:\s]*([^\n\r,]+)',
                r'\b([A-Z][A-Z\s&.,]+(?:INC|LTD|LLC|CORP|CO|COMPANY|GROUP))',
                r'\b([A-Z][A-Z\s&.,]+(?:INTERNATIONAL|INTL|GLOBAL|WORLD))'
            ],
            'port_of_loading': [
                r'\b(?:port\s+of\s+loading|port\s+of\s+export|loading\s+port)[:\s]*([^\n\r,]+)',
                r'\b(?:from\s+port|origin\s+port)[:\s]*([^\n\r,]+)',
                r'\b(?:departure|departing)[:\s]*([^\n\r,]+)',
                r'\b([A-Z][A-Z\s]+(?:PORT|HARBOR|TERMINAL))',
                r'\b([A-Z][A-Z\s]+,\s*[A-Z]{2})'
            ],
            'port_of_discharge': [
                r'\b(?:port\s+of\s+discharge|port\s+of\s+unloading|discharge\s+port)[:\s]*([^\n\r,]+)',
                r'\b(?:to\s+port|destination\s+port)[:\s]*([^\n\r,]+)',
                r'\b(?:arrival|arriving)[:\s]*([^\n\r,]+)',
                r'\b(?:foreign\s+port\s+of\s+unloading)[:\s]*([^\n\r,]+)',
                r'\b([A-Z][A-Z\s]+(?:PORT|HARBOR|TERMINAL))',
                r'\b([A-Z][A-Z\s]+,\s*[A-Z]{2})'
            ],
            'bl_number': [
                r'\b(?:bl\s*number|bill\s+of\s+lading\s+number|bol\s+number)[:\s]*([A-Z0-9\-]+)',
                r'\b(?:awb\s*number|air\s+waybill\s+number)[:\s]*([A-Z0-9\-]+)',
                r'\b([A-Z]{2,4}[0-9]{6,8})',
                r'\b([A-Z0-9]{8,12})'
            ],
            'flight_or_vessel': [
                r'\b(?:vessel|ship|carrier)[:\s]*([^\n\r,]+)',
                r'\b(?:flight|airline)[:\s]*([^\n\r,]+)',
                r'\b([A-Z]{2,4}\s+[A-Z0-9]+)',
                r'\b([A-Z][A-Z\s]+v\.[0-9]+)',
                r'\b([A-Z][A-Z\s]+v[0-9]+)'
            ],
            'container_numbers': [
                r'\b([A-Z]{4}[UZ][0-9]{7})',
                r'\b(?:container|contr)[:\s]*([A-Z0-9]+)',
                r'\b([A-Z]{4}[0-9]{7})',
                r'\b([A-Z]{3}[UZ][0-9]{6})'
            ]
        }
        
        # Weight patterns for post-processing
        self.weight_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?)\b',
            r'\b(\d+(?:\.\d+)?)\s*(lbs?|pounds?)\b',
            r'\bweight[:\s]*(\d+(?:\.\d+)?)\s*(kg|kgs|lbs?|pounds?)\b',
            r'\bgross\s*weight[:\s]*(\d+(?:\.\d+)?)\s*(kg|kgs|lbs?|pounds?)\b',
            r'\btotal\s*weight[:\s]*(\d+(?:\.\d+)?)\s*(kg|kgs|lbs?|pounds?)\b',
            r'\b(\d+(?:\.\d+)?)\s*kgs?\b',  # Common format in BOLs
            r'\b(\d+(?:\.\d+)?)\s*kg\s*/\s*\d+(?:\.\d+)?\s*cbm\b',  # Weight/CBM format
            r'\b(\d+(?:\.\d+)?)\s*kgs?\s*/\s*\d+(?:\.\d+)?\s*cbm\b',  # KGS/CBM format
            # AWB-specific patterns
            r'\bgross\s*weight[:\s]*(\d+(?:\.\d+)?)\s*k\b',  # "Gross Weight: 324 K"
            r'\b(\d+(?:\.\d+)?)\s*k\b',  # "324 K" (AWB format)
            r'\bweight[:\s]*(\d+(?:\.\d+)?)\s*k\b',  # "Weight: 324 K"
            r'\btotal[:\s]*(\d+(?:\.\d+)?)\s*k\b',  # "Total: 324 K"
            # Additional patterns for better extraction
            r'\bGROSS\s*WEIGHT[:\s]*(\d+(?:\.\d+)?)\b',
            r'\bWEIGHT[:\s]*(\d+(?:\.\d+)?)\b',
            r'\b(\d+(?:\.\d+)?)\s*KGS?\b'
        ]
        
        # Charge table for different shipment types and container types
        self.charge_table = {
            'air': {
                'base_rate': 5.0,  # $5 per kg
                'service_fee': 50.0,
                'min_fee': 100.0
            },
            'ocean': {
                '20ft': {
                    'ctn_fee': 150.0,
                    'service_fee': 75.0
                },
                '40ft': {
                    'ctn_fee': 200.0,
                    'service_fee': 100.0
                },
                '40ft_hc': {
                    'ctn_fee': 250.0,
                    'service_fee': 125.0
                },
                'loose_cargo': {
                    'rate_per_kg': 2.0,
                    'service_fee': 50.0
                }
            },
            'loose_cargo': {
                'rate_per_kg': 3.0,
                'service_fee': 75.0,
                'min_fee': 150.0
            }
        }

    def validate_fields(self, fields: Dict, document_type: str) -> ValidationResult:
        """Validate if all required fields are present"""
        required = self.required_fields.get(document_type, self.required_fields['BOL'])
        missing_fields = []
        
        for field in required:
            value = fields.get(field, '')
            if not value or value.strip() == '' or value == 'N/A':
                missing_fields.append(field)
        
        # Check for critical missing fields
        critical_missing = any(field in missing_fields for field in self.critical_fields)
        
        # Calculate confidence score
        total_fields = len(required)
        present_fields = total_fields - len(missing_fields)
        confidence_score = present_fields / total_fields if total_fields > 0 else 0.0
        
        # Determine if revalidation is needed
        needs_revalidation = len(missing_fields) > 0 and confidence_score < 0.8
        
        return ValidationResult(
            missing_fields=missing_fields,
            has_critical_missing=critical_missing,
            confidence_score=confidence_score,
            needs_revalidation=needs_revalidation
        )

    def extract_with_regex(self, text: str, field: str) -> List[str]:
        """Extract field using enhanced regex patterns"""
        patterns = self.enhanced_patterns.get(field, [])
        results = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle groups
                    for group in match:
                        if group and len(group.strip()) > 2:
                            results.append(group.strip())
                else:
                    if match and len(match.strip()) > 2:
                        results.append(match.strip())
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(results))

    def revalidate_with_enhanced_prompt(self, pdf_path: str, missing_fields: List[str], 
                                      original_result: Dict) -> Dict:
        """Re-validate with enhanced prompts for missing fields"""
        try:
            pdf = fitz.open(pdf_path)
            all_text = "\n".join(page.get_text() for page in pdf)
            
            if not all_text.strip():
                # Use Vision API for re-validation
                return self.revalidate_with_vision(pdf, missing_fields, original_result)
            
            # Create enhanced prompt for missing fields
            missing_fields_str = ', '.join(missing_fields)
            enhanced_prompt = f"""
You are an expert in logistics document processing. I need you to re-analyze this shipping document and focus specifically on extracting the following MISSING fields: {missing_fields_str}

IMPORTANT INSTRUCTIONS FOR MISSING FIELDS:

1. **Shipper**: Look for "SHIPPER", "EXPORTER", "CONSIGNOR", "FROM", "SENDER" sections. Extract ONLY the company name (not the address). Common patterns: "SHIPPER: COMPANY NAME" or "EXPORTER: COMPANY NAME"

2. **Consignee**: Look for "CONSIGNEE", "CONSIGNED TO", "TO", "RECIPIENT", "BUYER" sections. Extract ONLY the company name (not the address). Common patterns: "CONSIGNED TO: COMPANY NAME" or "CONSIGNEE: COMPANY NAME"

3. **Port of Loading**: Look for "PORT OF LOADING", "PORT OF EXPORT", "LOADING PORT", "FROM PORT", "ORIGIN PORT" sections. Extract the port name and country if available.

4. **Port of Discharge**: Look for "PORT OF DISCHARGE", "PORT OF UNLOADING", "DISCHARGE PORT", "TO PORT", "DESTINATION PORT", "FOREIGN PORT OF UNLOADING" sections. Extract the port name and country if available.

5. **BL Number**: Look for "BL NUMBER", "BILL OF LADING NUMBER", "BOL NUMBER", "AWB NUMBER", "AIR WAYBILL NUMBER" sections. Extract the complete number.

6. **Flight or Vessel**: Look for "VESSEL", "SHIP", "CARRIER", "FLIGHT", "AIRLINE" sections. Extract vessel names like "OOCL BERLIN v.041E" or flight numbers.

7. **Container Numbers**: Look for "CONTAINER", "CONTR", "MARKS AND NUMBERS" sections. Extract container numbers like "OOCU7645789", "TGBU8072614", etc.

CURRENT EXTRACTED DATA:
{json.dumps(original_result, indent=2)}

DOCUMENT TEXT:
{all_text}

Return ONLY a JSON object with the MISSING fields. If a field is still not found, use an empty string. Do not include fields that were already successfully extracted.
"""
            
            messages = [
                {"role": "system", "content": "You're an expert shipping document parser specializing in finding missing information."},
                {"role": "user", "content": enhanced_prompt},
            ]
            
            content = openai_call_with_fallback_old_api(messages, temperature=0.0)
            
            try:
                revalidation_data = json.loads(content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        revalidation_data = json.loads(match.group(0))
                    except Exception:
                        logger.error(f"Revalidation JSON parsing failed: {content}")
                        return original_result
                else:
                    logger.error(f"Revalidation failed: {content}")
                    return original_result
            
            # Merge revalidation results with original results
            merged_result = original_result.copy()
            for field in missing_fields:
                if field in revalidation_data and revalidation_data[field]:
                    merged_result[field] = revalidation_data[field]
                    logger.info(f"Revalidation found {field}: {revalidation_data[field]}")
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Revalidation failed: {e}")
            return original_result

    def revalidate_with_vision(self, pdf, missing_fields: List[str], original_result: Dict) -> Dict:
        """Re-validate using Vision API for missing fields"""
        try:
            import base64
            page = pdf[0]
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            
            missing_fields_str = ', '.join(missing_fields)
            vision_prompt = f"""
Re-analyze this shipping document image and focus specifically on extracting these MISSING fields: {missing_fields_str}

IMPORTANT: Look carefully for these specific fields that were missed in the first extraction:

1. **Shipper**: Look for "SHIPPER", "EXPORTER", "CONSIGNOR" sections
2. **Consignee**: Look for "CONSIGNEE", "CONSIGNED TO" sections  
3. **Port of Loading**: Look for "PORT OF LOADING", "PORT OF EXPORT" sections
4. **Port of Discharge**: Look for "PORT OF DISCHARGE", "PORT OF UNLOADING" sections
5. **BL Number**: Look for "BL NUMBER", "BILL OF LADING NUMBER" sections
6. **Flight or Vessel**: Look for "VESSEL", "SHIP", "CARRIER" sections
7. **Container Numbers**: Look for "CONTAINER", "MARKS AND NUMBERS" sections

CURRENT EXTRACTED DATA:
{json.dumps(original_result, indent=2)}

Return ONLY a JSON object with the MISSING fields. If a field is still not found, use an empty string.
"""
            
            messages = [
                {"role": "system", "content": "You're an expert shipping document parser specializing in finding missing information."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                    ]
                }
            ]
            
            vision_content = openai_call_with_fallback_old_api(messages, max_tokens=1024)
            
            try:
                revalidation_data = json.loads(vision_content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', vision_content, re.DOTALL)
                if match:
                    try:
                        revalidation_data = json.loads(match.group(0))
                    except Exception:
                        logger.error(f"Vision revalidation JSON parsing failed: {vision_content}")
                        return original_result
                else:
                    logger.error(f"Vision revalidation failed: {vision_content}")
                    return original_result
            
            # Merge revalidation results with original results
            merged_result = original_result.copy()
            for field in missing_fields:
                if field in revalidation_data and revalidation_data[field]:
                    merged_result[field] = revalidation_data[field]
                    logger.info(f"Vision revalidation found {field}: {revalidation_data[field]}")
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Vision revalidation failed: {e}")
            return original_result

    def extract_container_info(self, text: str, container_numbers: List[str]) -> ContainerInfo:
        """Extract container information from text with improved patterns"""
        container_types = []
        confidence = 0.0
        
        # Extract container types from text
        for container_type, patterns in self.container_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    container_types.append(container_type)
                    break
        
        # Remove duplicates while preserving order
        container_types = list(dict.fromkeys(container_types))
        
        # Calculate container count
        container_count = len(container_numbers) if container_numbers else 0
        
        # If no container numbers but container types found, estimate count
        if container_count == 0 and container_types:
            # Look for quantity patterns like "2X40'HQ", "1 x 20ST", etc.
            quantity_patterns = [
                r'(\d+)\s*[Xx]\s*40\s*[\'`]\s*hq',
                r'(\d+)\s*[Xx]\s*40\s*[\'`]\s*hc',
                r'(\d+)\s*[Xx]\s*20\s*[\'`]',
                r'(\d+)\s*x\s*20\s*ST',
                r'(\d+)\s*x\s*40\s*HIGH\s*CUBE',
                r'(\d+)\s*x\s*45\s*HIGH\s*CUBE'
            ]
            
            for pattern in quantity_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        container_count = sum(int(match) for match in matches)
                        break
                    except ValueError:
                        continue
        
        # Calculate confidence based on found information
        if container_numbers and container_types:
            confidence = 0.9
        elif container_numbers or container_types:
            confidence = 0.7
        elif container_count > 0:
            confidence = 0.5
        else:
            confidence = 0.3
        
        return ContainerInfo(
            container_numbers=container_numbers,
            container_types=container_types,
            container_count=container_count,
            confidence=confidence
        )

    def extract_weight_info(self, text: str) -> WeightInfo:
        """Extract weight information from text with improved patterns"""
        total_weight_kg = None
        weight_unit = 'kg'
        confidence = 0.0
        
        # Try to find weight patterns
        for pattern in self.weight_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        weight_str, unit = match
                    else:
                        weight_str = match
                        unit = 'kg'  # Default to kg
                    
                    try:
                        weight = float(weight_str)
                        
                        # Convert to kg if needed
                        if unit.lower() in ['lbs', 'pound', 'pounds']:
                            weight = weight * 0.453592  # Convert lbs to kg
                            weight_unit = 'lbs'
                        elif unit.lower() == 'k':
                            weight = weight * 0.453592  # Convert K (AWB format) to kg
                            weight_unit = 'k'
                        else:
                            weight_unit = 'kg'
                        
                        # Use the largest weight found (likely total weight)
                        if total_weight_kg is None or weight > total_weight_kg:
                            total_weight_kg = weight
                            
                    except ValueError:
                        continue
        
        # Calculate confidence
        if total_weight_kg:
            confidence = 0.8
        else:
            confidence = 0.2
        
        return WeightInfo(
            total_weight_kg=total_weight_kg,
            weight_unit=weight_unit,
            confidence=confidence
        )

    def classify_shipment_type(self, text: str, document_type: str) -> ShipmentInfo:
        """Classify shipment type based on document content"""
        text_lower = text.lower()
        confidence = 0.0
        
        # Check for air shipment indicators
        air_indicators = [
            'air waybill', 'awb', 'air freight', 'air cargo', 'flight',
            'airport', 'airline', 'aircraft', 'air mail', 'air waybill'
        ]
        
        # Check for ocean shipment indicators
        ocean_indicators = [
            'bill of lading', 'bol', 'ocean freight', 'vessel', 'ship',
            'container', 'port', 'shipping line', 'carrier', 'sea waybill'
        ]
        
        # Check for loose cargo indicators
        loose_indicators = [
            'loose cargo', 'break bulk', 'bulk cargo', 'general cargo',
            'non-containerized', 'pallet', 'crate', 'rolls', 'packages'
        ]
        
        # Count matches for each type
        air_matches = sum(1 for indicator in air_indicators if indicator in text_lower)
        ocean_matches = sum(1 for indicator in ocean_indicators if indicator in text_lower)
        loose_matches = sum(1 for indicator in loose_indicators if indicator in text_lower)
        
        # Determine shipment type
        if document_type == 'AWB' or air_matches > ocean_matches:
            shipment_type = 'air'
            confidence = 0.9 if air_matches > 0 else 0.7
        elif loose_matches > ocean_matches:
            shipment_type = 'loose_cargo'
            confidence = 0.8 if loose_matches > 0 else 0.6
        else:
            shipment_type = 'ocean'
            confidence = 0.9 if ocean_matches > 0 else 0.7
        
        return ShipmentInfo(
            shipment_type=shipment_type,
            confidence=confidence
        )

    def calculate_fees_with_charge_table(self, container_info: ContainerInfo, weight_info: WeightInfo, 
                                       shipment_info: ShipmentInfo) -> Dict:
        """Calculate fees using the charge table with different rates for different types"""
        
        # Default values
        ctn_fee = 100.0
        service_fee = 100.0
        total_fee = 200.0
        pricing_method = 'default'
        calculation_details = {
            'method': 'default',
            'reason': 'No specific pricing data available'
        }
        
        # Get charge rates based on shipment type
        if shipment_info.shipment_type == 'air':
            # Air freight pricing
            rates = self.charge_table['air']
            if weight_info.total_weight_kg:
                ctn_fee = max(weight_info.total_weight_kg * rates['base_rate'], rates['min_fee'])
                service_fee = rates['service_fee']
                pricing_method = 'air_kg'
                calculation_details = {
                    'method': 'air_kg',
                    'weight_kg': weight_info.total_weight_kg,
                    'rate_per_kg': rates['base_rate'],
                    'service_fee': rates['service_fee'],
                    'min_fee': rates['min_fee']
                }
        
        elif shipment_info.shipment_type == 'loose_cargo':
            # Loose cargo pricing
            rates = self.charge_table['loose_cargo']
            if weight_info.total_weight_kg:
                ctn_fee = max(weight_info.total_weight_kg * rates['rate_per_kg'], rates['min_fee'])
                service_fee = rates['service_fee']
                pricing_method = 'loose_cargo_kg'
                calculation_details = {
                    'method': 'loose_cargo_kg',
                    'weight_kg': weight_info.total_weight_kg,
                    'rate_per_kg': rates['rate_per_kg'],
                    'service_fee': rates['service_fee'],
                    'min_fee': rates['min_fee']
                }
        
        else:
            # Ocean freight pricing
            ocean_rates = self.charge_table['ocean']
            
            if container_info.container_count > 0 and container_info.container_types:
                # Container-based pricing
                total_ctn_fee = 0
                total_service_fee = 0
                
                for container_type in container_info.container_types:
                    if container_type in ocean_rates:
                        total_ctn_fee += ocean_rates[container_type]['ctn_fee']
                        total_service_fee += ocean_rates[container_type]['service_fee']
                
                ctn_fee = total_ctn_fee
                service_fee = total_service_fee
                pricing_method = 'ocean_container'
                calculation_details = {
                    'method': 'ocean_container',
                    'container_types': container_info.container_types,
                    'container_count': container_info.container_count,
                    'rates_used': {ct: ocean_rates[ct] for ct in container_info.container_types if ct in ocean_rates}
                }
            
            elif weight_info.total_weight_kg:
                # Weight-based pricing for ocean
                rates = ocean_rates['loose_cargo']
                ctn_fee = weight_info.total_weight_kg * rates['rate_per_kg']
                service_fee = rates['service_fee']
                pricing_method = 'ocean_kg'
                calculation_details = {
                    'method': 'ocean_kg',
                    'weight_kg': weight_info.total_weight_kg,
                    'rate_per_kg': rates['rate_per_kg'],
                    'service_fee': rates['service_fee']
                }
        
        total_fee = ctn_fee + service_fee
        
        return {
            'ctn_fee': ctn_fee,
            'service_fee': service_fee,
            'total_fee': total_fee,
            'pricing_method': pricing_method,
            'calculation_details': calculation_details
        }

    def extract_fields_with_correct_api(self, pdf_path: str) -> Dict:
        """Extract fields using the correct OpenAI API format"""
        import fitz
        import json
        
        try:
            pdf = fitz.open(pdf_path)
            all_text = "\n".join(page.get_text() for page in pdf)
            
            # If text is empty, go straight to Vision
            if not all_text.strip():
                # No text extracted from PDF, falling back to Vision API directly
                return call_openai_vision_fallback(pdf, all_text)

            prompt = f"""
You are an expert in logistics document processing. Given the following text from a shipping document, extract:
- document_type: (BOL or AWB)
- bl_number
- shipper
- consignee: Look for "CONSIGNED TO" or "CONSIGNEE" sections. Extract ONLY the company name (not the address). If you see "CONSIGNED TO" followed by a company name, that is the consignee. Do not include address information, phone numbers, or other details - just the company name.
- port_of_loading
- port_of_discharge
- container_numbers: Look for container numbers like "OOCU7645789", "TGBU8072614", etc. Extract all container numbers found.
- flight_or_vessel: Look for vessel names like "OOCL BERLIN v.041E" or flight numbers
- product_description
- paid_amount: the payment amount shown on the document (e.g., $420, 420 USD, Amount: 420, etc)

IMPORTANT: For consignee extraction, pay special attention to:
1. "CONSIGNED TO" sections - this is the primary consignee
2. "CONSIGNEE" sections
3. Company names that appear after these labels

TEXT:\n{all_text}

Return a valid JSON object with these fields. If a field is missing, use an empty string.
"""
            # Calling OpenAI API for OCR...
            messages = [
                {"role": "system", "content": "You're an expert shipping document parser."},
                {"role": "user", "content": prompt},
            ]
            content = openai_call_with_fallback_old_api(messages, temperature=0.0)
            # OpenAI API response received
            
            try:
                data = json.loads(content)
            except Exception:
                import re
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(0))
                    except Exception:
                        logger.info("[DEBUG] Regex fallback failed, falling back to Vision API...")
                        return call_openai_vision_fallback(pdf, all_text)
                else:
                    logger.info("[DEBUG] No JSON found in response, falling back to Vision API...")
                    return call_openai_vision_fallback(pdf, all_text)

            data['raw_text'] = all_text
            for field in ['document_type', 'bl_number', 'shipper', 'consignee', 'port_of_loading', 
                         'port_of_discharge', 'container_numbers', 'flight_or_vessel', 'product_description', 'paid_amount']:
                if field not in data:
                    data[field] = ''
            
            if all(data.get(field, '') == '' for field in ['bl_number', 'shipper', 'consignee', 'port_of_loading', 
                                                          'port_of_discharge', 'container_numbers', 'flight_or_vessel']):
                logger.info("[DEBUG] Text extraction returned all empty, falling back to Vision API...")
                return call_openai_vision_fallback(pdf, all_text)

            # extract_fields_with_correct_api returning data
            return data
            
        except Exception as e:
            logger.error(f"[OpenAI OCR] Error: {e}")
            return {
                'document_type': 'BOL',
                'bl_number': '',
                'shipper': '',
                'consignee': '',
                'port_of_loading': '',
                'port_of_discharge': '',
                'container_numbers': [],
                'flight_or_vessel': '',
                'product_description': '',
                'paid_amount': '',
                'raw_text': ''
            }

    def extract_fields_openai_enhanced_v5(self, pdf_path: str) -> Dict:
        """Enhanced AI-based field extraction V5 - Re-validation system"""
        
        # Use enhanced AI extraction with correct API format
        try:
            basic_fields = self.extract_fields_with_correct_api(pdf_path)
            # Original AI extraction successful
        except Exception as e:
            logger.error(f"Original AI extraction failed: {e}")
            # Return minimal result
            basic_fields = {
                'document_type': 'BOL',
                'bl_number': '',
                'shipper': '',
                'consignee': '',
                'port_of_loading': '',
                'port_of_discharge': '',
                'container_numbers': [],
                'flight_or_vessel': '',
                'product_description': '',
                'paid_amount': '',
                'raw_text': ''
            }
        
        # Validate fields
        document_type = basic_fields.get('document_type', 'BOL')
        validation_result = self.validate_fields(basic_fields, document_type)
        
        # Field validation: {validation_result.missing_fields} missing, confidence: {validation_result.confidence_score:.2f}
        
        # If revalidation is needed, attempt to find missing fields
        if validation_result.needs_revalidation:
            logger.info(f"Revalidation needed for fields: {validation_result.missing_fields}")
            
            # First try regex extraction for missing fields
            text = basic_fields.get('raw_text', '')
            regex_improvements = {}
            
            for field in validation_result.missing_fields:
                regex_results = self.extract_with_regex(text, field)
                if regex_results:
                    regex_improvements[field] = regex_results[0]  # Take first result
                    logger.info(f"Regex found {field}: {regex_results[0]}")
            
            # Apply regex improvements
            for field, value in regex_improvements.items():
                basic_fields[field] = value
            
            # Re-validate after regex improvements
            validation_result = self.validate_fields(basic_fields, document_type)
            
            # If still missing fields, try enhanced AI revalidation
            if validation_result.needs_revalidation:
                logger.info(f"Still missing fields after regex, trying AI revalidation: {validation_result.missing_fields}")
                basic_fields = self.revalidate_with_enhanced_prompt(pdf_path, validation_result.missing_fields, basic_fields)
                
                # Final validation
                validation_result = self.validate_fields(basic_fields, document_type)
        
        # Extract text for post-processing
        text = basic_fields.get('raw_text', '')
        
        # Parse container numbers with improved logic
        container_numbers_raw = basic_fields.get('container_numbers', [])
        
        # Parse container numbers with improved logic
        container_numbers = []
        if isinstance(container_numbers_raw, str):
            # Handle string format
            if container_numbers_raw and container_numbers_raw != 'N/A':
                # Split by common delimiters
                for c in re.split(r'[,;\s]+', container_numbers_raw):
                    c = c.strip()
                    if c and len(c) >= 4:
                        container_numbers.append(c)
        elif isinstance(container_numbers_raw, list):
            for c in container_numbers_raw:
                if c:
                    c_str = str(c).strip()
                    # Handle container numbers with slashes
                    if '/' in c_str:
                        container_num = c_str.split('/')[0].strip()
                        if len(container_num) >= 4:
                            container_numbers.append(container_num)
                    else:
                        if len(c_str) >= 4:
                            container_numbers.append(c_str)
        
        # Enhanced extraction
        container_info = self.extract_container_info(text, container_numbers)
        weight_info = self.extract_weight_info(text)
        shipment_info = self.classify_shipment_type(text, document_type)
        
        # Calculate fees using charge table
        fee_calculation = self.calculate_fees_with_charge_table(container_info, weight_info, shipment_info)
        
        # Calculate overall confidence
        overall_confidence = (
            container_info.confidence * 0.3 +
            weight_info.confidence * 0.2 +
            shipment_info.confidence * 0.2 +
            validation_result.confidence_score * 0.3  # Include field validation confidence
        )
        
        # Determine extraction method
        extraction_method = 'ai'
        if '[OpenAI Vision fallback used]' in text:
            extraction_method = 'vision_api'
        
        # Prepare enhanced result
        enhanced_fields = {
            # Original fields
            **basic_fields,
            
            # Update container_numbers based on shipment type
            'container_numbers': 'N/A' if shipment_info.shipment_type == 'air' else (', '.join(container_numbers) if isinstance(container_numbers, list) else str(container_numbers)),
            
            # Enhanced container info
            'container_count': 0 if shipment_info.shipment_type == 'air' else container_info.container_count,
            'container_types': [] if shipment_info.shipment_type == 'air' else container_info.container_types,
            'container_type': None if shipment_info.shipment_type == 'air' else (container_info.container_types[0] if container_info.container_types else None),
            'container_count_20ft': 0 if shipment_info.shipment_type == 'air' else container_info.container_types.count('20ft'),
            'container_count_40ft': 0 if shipment_info.shipment_type == 'air' else container_info.container_types.count('40ft'),
            'container_count_40ft_hc': 0 if shipment_info.shipment_type == 'air' else container_info.container_types.count('40ft_hc'),
            
            # Enhanced weight info
            'total_weight_kg': float(weight_info.total_weight_kg) if weight_info.total_weight_kg else None,
            'weight_unit': weight_info.weight_unit,
            
            # Enhanced shipment info
            'shipment_type': shipment_info.shipment_type,
            'pricing_method': fee_calculation['pricing_method'],
            
            # Calculated fees using charge table
            'calculated_ctn_fee': float(fee_calculation['ctn_fee']) if fee_calculation['ctn_fee'] else None,
            'calculated_service_fee': float(fee_calculation['service_fee']) if fee_calculation['service_fee'] else None,
            'calculated_total_fee': float(fee_calculation['total_fee']) if fee_calculation['total_fee'] else None,
            
            # Confidence and audit info
            'ocr_confidence_score': float(overall_confidence) if overall_confidence else None,
            'pricing_calculation_log': fee_calculation['calculation_details'],
            
            # Validation info
            'validation_result': {
                'missing_fields': validation_result.missing_fields,
                'has_critical_missing': validation_result.has_critical_missing,
                'confidence_score': float(validation_result.confidence_score),
                'needs_revalidation': validation_result.needs_revalidation,
                'revalidation_performed': validation_result.needs_revalidation
            },
            
            # Confidence breakdown
            'confidence_breakdown': {
                'container_detection': float(container_info.confidence) if container_info.confidence else None,
                'weight_detection': float(weight_info.confidence) if weight_info.confidence else None,
                'shipment_classification': float(shipment_info.confidence) if shipment_info.confidence else None,
                'field_validation': float(validation_result.confidence_score),
                'overall': float(overall_confidence) if overall_confidence else None
            },
            
            # Extraction method info
            'extraction_method': extraction_method
        }
        
        # Enhanced AI OCR V5 completed with confidence: {overall_confidence:.2f}
        return enhanced_fields

# Global instance
enhanced_ai_ocr_v5 = EnhancedAIOCRProcessorV5()

def extract_fields_openai_enhanced_v5(pdf_path: str) -> Dict:
    """Enhanced AI-based field extraction V5 - Re-validation system"""
    return enhanced_ai_ocr_v5.extract_fields_openai_enhanced_v5(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor_enhanced_v5.py <pdf_path>")
        sys.exit(1)
    
    result = extract_fields_openai_enhanced_v5(sys.argv[1])
    print(json.dumps(result, indent=2)) 