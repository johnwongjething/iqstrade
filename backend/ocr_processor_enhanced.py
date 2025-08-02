#!/usr/bin/env python3
"""
Enhanced OCR Processor - AI-Based with Additional Fields
Combines the superior AI-based approach with all enhanced fields
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ocr_processor import extract_fields_openai, openai_call_with_fallback
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

class EnhancedAIOCRProcessor:
    """Enhanced AI-based OCR processor with container and weight detection"""
    
    def __init__(self):
        # Container type patterns for post-processing
        self.container_patterns = {
            '20ft': [
                r'\b20\s*ft\b',
                r'\b20\s*feet\b',
                r'\b20\'\b',
                r'\b20\s*foot\b'
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
                r'\b2\s*[Xx]\s*40\s*[\'`]\s*hc\b'
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
            r'\btotal[:\s]*(\d+(?:\.\d+)?)\s*k\b'  # "Total: 324 K"
        ]

    def extract_container_info(self, text: str, container_numbers: List[str]) -> ContainerInfo:
        """Extract container information from text"""
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
        
        # Calculate confidence based on found information
        if container_numbers and container_types:
            confidence = 0.9
        elif container_numbers or container_types:
            confidence = 0.6
        else:
            confidence = 0.3
        
        return ContainerInfo(
            container_numbers=container_numbers,
            container_types=container_types,
            container_count=container_count,
            confidence=confidence
        )

    def extract_weight_info(self, text: str) -> WeightInfo:
        """Extract weight information from text"""
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
            'airport', 'airline', 'aircraft', 'air mail'
        ]
        
        # Check for ocean shipment indicators
        ocean_indicators = [
            'bill of lading', 'bol', 'ocean freight', 'vessel', 'ship',
            'container', 'port', 'shipping line', 'carrier'
        ]
        
        # Check for loose cargo indicators
        loose_indicators = [
            'loose cargo', 'break bulk', 'bulk cargo', 'general cargo',
            'non-containerized', 'pallet', 'crate'
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

    def calculate_fees(self, container_info: ContainerInfo, weight_info: WeightInfo, 
                      shipment_info: ShipmentInfo) -> Dict:
        """Calculate fees based on container and weight information"""
        
        # Default fees
        ctn_fee = 100.0
        service_fee = 100.0
        total_fee = 200.0
        pricing_method = 'container'
        calculation_details = {
            'method': 'default',
            'reason': 'No specific pricing data available'
        }
        
        # Calculate based on shipment type
        if shipment_info.shipment_type == 'air':
            # Air freight pricing
            if weight_info.total_weight_kg:
                # $5 per kg for air freight
                ctn_fee = weight_info.total_weight_kg * 5.0
                service_fee = 50.0
                pricing_method = 'kg'
                calculation_details = {
                    'method': 'air_kg',
                    'weight_kg': weight_info.total_weight_kg,
                    'rate_per_kg': 5.0,
                    'service_fee': 50.0
                }
        else:
            # Ocean freight pricing
            if container_info.container_count > 0:
                # $100 per container
                ctn_fee = container_info.container_count * 100.0
                service_fee = 50.0 * container_info.container_count
                pricing_method = 'container'
                calculation_details = {
                    'method': 'ocean_container',
                    'container_count': container_info.container_count,
                    'rate_per_container': 100.0,
                    'service_fee_per_container': 50.0
                }
            elif weight_info.total_weight_kg:
                # $2 per kg for ocean freight
                ctn_fee = weight_info.total_weight_kg * 2.0
                service_fee = 50.0
                pricing_method = 'kg'
                calculation_details = {
                    'method': 'ocean_kg',
                    'weight_kg': weight_info.total_weight_kg,
                    'rate_per_kg': 2.0,
                    'service_fee': 50.0
                }
        
        total_fee = ctn_fee + service_fee
        
        return {
            'ctn_fee': ctn_fee,
            'service_fee': service_fee,
            'total_fee': total_fee,
            'pricing_method': pricing_method,
            'calculation_details': calculation_details
        }

    def extract_fields_openai_enhanced(self, pdf_path: str) -> Dict:
        """Enhanced AI-based field extraction with additional fields"""
        
        # First, get basic fields using the original AI approach
        basic_fields = extract_fields_openai(pdf_path)
        
        # Extract text for post-processing
        text = basic_fields.get('raw_text', '')
        container_numbers_raw = basic_fields.get('container_numbers', [])
        document_type = basic_fields.get('document_type', 'BOL')
        
        # Parse container numbers
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
            container_numbers = []
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
        
        # Calculate fees
        fee_calculation = self.calculate_fees(container_info, weight_info, shipment_info)
        
        # Calculate overall confidence
        overall_confidence = (
            container_info.confidence * 0.4 +
            weight_info.confidence * 0.3 +
            shipment_info.confidence * 0.3
        )
        
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
            
            # Calculated fees
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
            }
        }
        
        logger.info(f"Enhanced AI OCR completed with confidence: {overall_confidence:.2f}")
        return enhanced_fields

# Global instance
enhanced_ai_ocr = EnhancedAIOCRProcessor()

def extract_fields_openai_enhanced(pdf_path: str) -> Dict:
    """Enhanced AI-based field extraction with additional fields"""
    return enhanced_ai_ocr.extract_fields_openai_enhanced(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor_enhanced.py <pdf_path>")
        sys.exit(1)
    
    result = extract_fields_openai_enhanced(sys.argv[1])
    print(json.dumps(result, indent=2)) 