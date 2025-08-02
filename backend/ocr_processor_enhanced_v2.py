#!/usr/bin/env python3
"""
Enhanced OCR Processor V2 - AI-Based with Improved Field Extraction
Fixes missing fields, implements charge tables, and improves image-based PDF handling
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

class EnhancedAIOCRProcessorV2:
    """Enhanced AI-based OCR processor with improved field extraction and charge tables"""
    
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

    def extract_fields_openai_enhanced_v2(self, pdf_path: str) -> Dict:
        """Enhanced AI-based field extraction with smart fallback to heavy regex"""
        
        # First, try to get basic fields using the original AI approach
        basic_fields = {}
        ai_success = False
        
        try:
            basic_fields = extract_fields_openai(pdf_path)
            ai_success = True
            logger.info("AI extraction successful")
        except Exception as e:
            logger.warning(f"OpenAI text extraction failed: {e}")
            # Fallback to Vision API for image-based PDFs
            try:
                pdf = fitz.open(pdf_path)
                basic_fields = call_openai_vision_fallback(pdf, "")
                ai_success = True
                logger.info("Using Vision API fallback for image-based PDF")
            except Exception as vision_error:
                logger.error(f"Vision API fallback also failed: {vision_error}")
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
        
        # Check if we have meaningful text extraction
        has_meaningful_text = len(text.strip()) > 100 and any([
            basic_fields.get('consignee'),
            basic_fields.get('port_of_loading'),
            basic_fields.get('port_of_discharge'),
            basic_fields.get('bl_number'),
            basic_fields.get('container_numbers')
        ])
        
        # If AI failed or extracted minimal data, force heavy regex extraction
        if not ai_success or not has_meaningful_text:
            logger.info("AI extraction insufficient, forcing heavy regex extraction")
            return self._force_heavy_regex_extraction(pdf_path)
        
        # Continue with enhanced AI processing
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
            }
        }
        
        logger.info(f"Enhanced AI OCR V2 completed with confidence: {overall_confidence:.2f}")
        return enhanced_fields

    def _force_heavy_regex_extraction(self, pdf_path: str) -> Dict:
        """Force heavy regex extraction when AI fails"""
        logger.info("Starting heavy regex extraction")
        
        try:
            # Extract text using PyMuPDF (works for image-based PDFs)
            pdf = fitz.open(pdf_path)
            text = ""
            for page in pdf:
                text += page.get_text()
            pdf.close()
            
            logger.info(f"Extracted {len(text)} characters using PyMuPDF")
            
            # Heavy regex patterns for field extraction
            patterns = {
                'shipper': [
                    r'(?:2\.\s*EXPORTER|SHIPPER|SHIPPER\'S\s+NAME)[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
                    r'(?:SHIPPER|EXPORTER)[:\s]*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
                    r'(?:2\.\s*EXPORTER)[:\s]*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)'
                ],
                'consignee': [
                    r'(?:3\.\s*CONSIGNED\s+TO|CONSIGNEE|CONSIGNEE\'S\s+NAME)[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
                    r'(?:CONSIGNED\s+TO|CONSIGNEE)[:\s]*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
                    r'(?:3\.\s*CONSIGNED\s+TO)[:\s]*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)'
                ],
                'port_of_loading': [
                    r'(?:15\.\s*PORT\s+OF\s+LOADING|PORT\s+OF\s+LOADING)[:\s]*([A-Z\s]+)',
                    r'(?:PORT\s+OF\s+LOADING)[:\s]*([A-Z\s]+)',
                    r'(?:15\.\s*PORT\s+OF\s+LOADING)[:\s]*([A-Z\s]+)'
                ],
                'port_of_discharge': [
                    r'(?:16\.\s*FOREIGN\s+PORT\s+OF\s+UNLOADING|PORT\s+OF\s+DISCHARGE)[:\s]*([A-Z\s]+)',
                    r'(?:17\.\s*PLACE\s+OF\s+DELIVERY)[:\s]*([A-Z\s]+)',
                    r'(?:PORT\s+OF\s+DISCHARGE)[:\s]*([A-Z\s]+)',
                    r'(?:PLACE\s+OF\s+DELIVERY)[:\s]*([A-Z\s]+)'
                ],
                'bl_number': [
                    r'(?:5a\.\s*B/L\s+NUMBER|B/L\s+NUMBER|BL\s+NUMBER)[:\s]*([A-Z0-9]+)',
                    r'(?:B/L\s+NO|BL\s+NO)[:\s]*([A-Z0-9]+)',
                    r'(?:6\.\s*BL\s+NUMBER)[:\s]*([A-Z0-9]+)'
                ],
                'flight_or_vessel': [
                    r'(?:14\.\s*EXPORTING\s+CARRIER|VESSEL|FLIGHT)[:\s]*([A-Z\s0-9\.]+)',
                    r'(?:EXPORTING\s+CARRIER|VESSEL)[:\s]*([A-Z\s0-9\.]+)',
                    r'(?:OCEAN\s+VESSEL)[:\s]*([A-Z\s0-9\.]+)'
                ],
                'container_numbers': [
                    r'(?:CONTR\s*#|CONTAINER\s+NO)[:\s]*([A-Z0-9]+)',
                    r'(?:CONTAINER\s+NUMBER)[:\s]*([A-Z0-9]+)',
                    r'([A-Z]{4}[0-9]{7})',  # Standard container format
                    r'([A-Z]{3}[U][0-9]{7})'  # Another common format
                ],
                'total_weight': [
                    r'(?:21\.\s*GROSS\s+WEIGHT|GROSS\s+WEIGHT)[:\s]*(\d+(?:\.\d+)?)\s*(?:KGS?|KILOS?)',
                    r'(?:GROSS\s+WEIGHT)[:\s]*(\d+(?:\.\d+)?)\s*(?:KGS?|KILOS?)',
                    r'(\d+(?:\.\d+)?)\s*KGS?\s*/\s*\d+(?:\.\d+)?\s*CBM'
                ]
            }
            
            # Extract fields using regex
            extracted_fields = {}
            for field, field_patterns in patterns.items():
                for pattern in field_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        if field == 'container_numbers':
                            # Handle multiple container numbers
                            container_nums = []
                            for match in matches:
                                if isinstance(match, tuple):
                                    container_nums.extend([m for m in match if m])
                                else:
                                    container_nums.append(match)
                            extracted_fields[field] = ', '.join(container_nums) if container_nums else ''
                        else:
                            # Take the first match
                            match = matches[0]
                            if isinstance(match, tuple):
                                match = match[0]
                            extracted_fields[field] = match.strip()
                        break
                else:
                    extracted_fields[field] = ''
            
            # Extract container breakdown
            container_breakdown = self._extract_container_breakdown_regex(text)
            
            # Extract weight
            weight_kg = None
            for pattern in patterns['total_weight']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    try:
                        weight_kg = float(matches[0])
                        break
                    except ValueError:
                        continue
            
            # Determine shipment type
            shipment_type = 'ocean'
            if any(word in text.upper() for word in ['AIR WAYBILL', 'AWB', 'AIR FREIGHT']):
                shipment_type = 'air'
            elif any(word in text.upper() for word in ['LOOSE CARGO', 'BREAK BULK']):
                shipment_type = 'loose_cargo'
            
            # Calculate fees
            fee_calculation = self._calculate_fees_regex(container_breakdown, weight_kg, shipment_type)
            
            result = {
                'document_type': 'BOL',
                'shipper': extracted_fields.get('shipper', ''),
                'consignee': extracted_fields.get('consignee', ''),
                'port_of_loading': extracted_fields.get('port_of_loading', ''),
                'port_of_discharge': extracted_fields.get('port_of_discharge', ''),
                'bl_number': extracted_fields.get('bl_number', ''),
                'container_numbers': extracted_fields.get('container_numbers', ''),
                'flight_or_vessel': extracted_fields.get('flight_or_vessel', ''),
                'product_description': '',  # Would need more complex extraction
                'total_weight_kg': weight_kg,
                'shipment_type': shipment_type,
                'container_count': container_breakdown['total'],
                'container_count_20ft': container_breakdown['20ft'],
                'container_count_40ft': container_breakdown['40ft'],
                'container_count_40ft_hc': container_breakdown['40ft_hc'],
                'calculated_ctn_fee': fee_calculation['ctn_fee'],
                'calculated_service_fee': fee_calculation['service_fee'],
                'calculated_total_fee': fee_calculation['total_fee'],
                'pricing_method': fee_calculation['pricing_method'],
                'ocr_confidence_score': 0.6,  # Lower confidence for regex
                'pricing_calculation_log': fee_calculation['calculation_details'],
                'raw_text': text,
                'extraction_method': 'heavy_regex'
            }
            
            logger.info(f"Heavy regex extraction completed with {len(extracted_fields)} fields")
            return result
            
        except Exception as e:
            logger.error(f"Heavy regex extraction failed: {e}")
            # Return minimal result
            return {
                'document_type': 'BOL',
                'shipper': '',
                'consignee': '',
                'port_of_loading': '',
                'port_of_discharge': '',
                'bl_number': '',
                'container_numbers': '',
                'flight_or_vessel': '',
                'product_description': '',
                'total_weight_kg': None,
                'shipment_type': 'ocean',
                'container_count': 0,
                'container_count_20ft': 0,
                'container_count_40ft': 0,
                'container_count_40ft_hc': 0,
                'calculated_ctn_fee': 100.0,
                'calculated_service_fee': 100.0,
                'calculated_total_fee': 200.0,
                'pricing_method': 'default',
                'ocr_confidence_score': 0.1,
                'pricing_calculation_log': {'method': 'default', 'reason': 'Regex extraction failed'},
                'raw_text': '',
                'extraction_method': 'failed'
            }

    def _extract_container_breakdown_regex(self, text: str) -> Dict:
        """Extract container breakdown using regex patterns"""
        breakdown = {'20ft': 0, '40ft': 0, '40ft_hc': 0, 'total': 0}
        
        # Look for quantity patterns
        quantity_patterns = [
            (r'(\d+)\s*[Xx]\s*40\s*[\'`]\s*hq', '40ft_hc'),
            (r'(\d+)\s*[Xx]\s*40\s*[\'`]\s*hc', '40ft_hc'),
            (r'(\d+)\s*x\s*40\s*HIGH\s*CUBE', '40ft_hc'),
            (r'(\d+)\s*x\s*45\s*HIGH\s*CUBE', '40ft_hc'),
            (r'(\d+)\s*[Xx]\s*40\s*[\'`]', '40ft'),
            (r'(\d+)\s*x\s*40\s*FT', '40ft'),
            (r'(\d+)\s*[Xx]\s*20\s*[\'`]', '20ft'),
            (r'(\d+)\s*x\s*20\s*ST', '20ft'),
            (r'(\d+)\s*x\s*20\s*FT', '20ft'),
            (r'1\s*x\s*20\s*ST', '20ft'),
            (r'1\s*x\s*40\s*HIGH\s*CUBE', '40ft_hc'),
            (r'1\s*x\s*45\s*HIGH\s*CUBE', '40ft_hc')
        ]
        
        for pattern, container_type in quantity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    count = int(match) if match.isdigit() else 1
                    breakdown[container_type] += count
                    breakdown['total'] += count
                except ValueError:
                    breakdown[container_type] += 1
                    breakdown['total'] += 1
        
        return breakdown

    def _calculate_fees_regex(self, container_breakdown: Dict, weight_kg: float, shipment_type: str) -> Dict:
        """Calculate fees using regex-extracted data"""
        # Use the same charge table logic
        if shipment_type == 'air':
            rates = self.charge_table['air']
            if weight_kg:
                ctn_fee = max(weight_kg * rates['base_rate'], rates['min_fee'])
                service_fee = rates['service_fee']
                pricing_method = 'air_kg'
            else:
                ctn_fee = rates['min_fee']
                service_fee = rates['service_fee']
                pricing_method = 'air_default'
        elif shipment_type == 'loose_cargo':
            rates = self.charge_table['loose_cargo']
            if weight_kg:
                ctn_fee = max(weight_kg * rates['rate_per_kg'], rates['min_fee'])
                service_fee = rates['service_fee']
                pricing_method = 'loose_cargo_kg'
            else:
                ctn_fee = rates['min_fee']
                service_fee = rates['service_fee']
                pricing_method = 'loose_cargo_default'
        else:
            # Ocean freight
            ocean_rates = self.charge_table['ocean']
            if container_breakdown['total'] > 0:
                total_ctn_fee = 0
                total_service_fee = 0
                
                if container_breakdown['20ft'] > 0:
                    total_ctn_fee += container_breakdown['20ft'] * ocean_rates['20ft']['ctn_fee']
                    total_service_fee += container_breakdown['20ft'] * ocean_rates['20ft']['service_fee']
                
                if container_breakdown['40ft'] > 0:
                    total_ctn_fee += container_breakdown['40ft'] * ocean_rates['40ft']['ctn_fee']
                    total_service_fee += container_breakdown['40ft'] * ocean_rates['40ft']['service_fee']
                
                if container_breakdown['40ft_hc'] > 0:
                    total_ctn_fee += container_breakdown['40ft_hc'] * ocean_rates['40ft_hc']['ctn_fee']
                    total_service_fee += container_breakdown['40ft_hc'] * ocean_rates['40ft_hc']['service_fee']
                
                ctn_fee = total_ctn_fee
                service_fee = total_service_fee
                pricing_method = 'ocean_container'
            elif weight_kg:
                rates = ocean_rates['loose_cargo']
                ctn_fee = weight_kg * rates['rate_per_kg']
                service_fee = rates['service_fee']
                pricing_method = 'ocean_kg'
            else:
                ctn_fee = 100.0
                service_fee = 100.0
                pricing_method = 'ocean_default'
        
        total_fee = ctn_fee + service_fee
        
        return {
            'ctn_fee': ctn_fee,
            'service_fee': service_fee,
            'total_fee': total_fee,
            'pricing_method': pricing_method,
            'calculation_details': {
                'method': pricing_method,
                'container_breakdown': container_breakdown,
                'weight_kg': weight_kg,
                'shipment_type': shipment_type
            }
        }

# Global instance
enhanced_ai_ocr_v2 = EnhancedAIOCRProcessorV2()

def extract_fields_openai_enhanced_v2(pdf_path: str) -> Dict:
    """Enhanced AI-based field extraction V2 with improved field extraction and charge tables"""
    return enhanced_ai_ocr_v2.extract_fields_openai_enhanced_v2(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor_enhanced_v2.py <pdf_path>")
        sys.exit(1)
    
    result = extract_fields_openai_enhanced_v2(sys.argv[1])
    print(json.dumps(result, indent=2)) 