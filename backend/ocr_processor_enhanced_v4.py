#!/usr/bin/env python3
"""
Enhanced OCR Processor V4 - Merged Approach
Combines the original working OCR processor with enhanced features
Keeps the Vision API fallback that was working for image-based PDFs
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ocr_processor import extract_fields_openai, openai_call_with_fallback, call_openai_vision_fallback
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

class EnhancedAIOCRProcessorV4:
    """Enhanced AI-based OCR processor V4 - Merged approach"""
    
    def __init__(self):
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

    def extract_fields_openai_enhanced_v4(self, pdf_path: str) -> Dict:
        """Enhanced AI-based field extraction V4 - Merged approach with original fallback"""
        
        # Use the original extract_fields_openai which has the working Vision API fallback
        try:
            basic_fields = extract_fields_openai(pdf_path)
            logger.info("Original AI extraction successful")
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
        
        # Extract text for post-processing
        text = basic_fields.get('raw_text', '')
        
        # Parse container numbers with improved logic
        container_numbers_raw = basic_fields.get('container_numbers', [])
        document_type = basic_fields.get('document_type', 'BOL')
        
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
            container_info.confidence * 0.4 +
            weight_info.confidence * 0.3 +
            shipment_info.confidence * 0.3
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
            
            # Confidence breakdown
            'confidence_breakdown': {
                'container_detection': float(container_info.confidence) if container_info.confidence else None,
                'weight_detection': float(weight_info.confidence) if weight_info.confidence else None,
                'shipment_classification': float(shipment_info.confidence) if shipment_info.confidence else None,
                'overall': float(overall_confidence) if overall_confidence else None
            },
            
            # Extraction method info
            'extraction_method': extraction_method
        }
        
        logger.info(f"Enhanced AI OCR V4 completed with confidence: {overall_confidence:.2f}")
        return enhanced_fields

# Global instance
enhanced_ai_ocr_v4 = EnhancedAIOCRProcessorV4()

def extract_fields_openai_enhanced_v4(pdf_path: str) -> Dict:
    """Enhanced AI-based field extraction V4 - Merged approach with original fallback"""
    return enhanced_ai_ocr_v4.extract_fields_openai_enhanced_v4(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor_enhanced_v4.py <pdf_path>")
        sys.exit(1)
    
    result = extract_fields_openai_enhanced_v4(sys.argv[1])
    print(json.dumps(result, indent=2)) 