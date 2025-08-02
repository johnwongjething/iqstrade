#!/usr/bin/env python3
"""
Enhanced OCR Processor for IQSTrade
- Detects container types (20ft, 40ft, 40ft HC)
- Extracts weight information for loose cargo
- Identifies shipment types (ocean, air, loose cargo)
- Provides confidence scores for manual review
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ocr_processor import extract_fields_openai

# Make Google Vision import optional to avoid credential issues during testing
try:
    from extract_fields import extract_fields as extract_fields_legacy
    GOOGLE_VISION_AVAILABLE = True
except Exception as e:
    print(f"Warning: Google Vision not available: {e}")
    GOOGLE_VISION_AVAILABLE = False
    extract_fields_legacy = None

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
    total_weight_kg: float
    weight_unit: str  # 'kg' or 'lbs'
    confidence: float

@dataclass
class ShipmentInfo:
    """Shipment type and classification"""
    shipment_type: str  # 'ocean', 'air', 'loose_cargo'
    document_type: str  # 'BOL', 'AWB', 'Cargo Manifest'
    confidence: float

class EnhancedOCRProcessor:
    """Enhanced OCR processor with container and weight detection"""
    
    def __init__(self):
        # Container type patterns
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
        
        # Weight patterns
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
        
        # Shipment type indicators
        self.shipment_indicators = {
            'ocean': [
                'bill of lading',
                'bl number',
                'ocean vessel',
                'port of loading',
                'port of discharge',
                'container',
                'vessel'
            ],
            'air': [
                'air waybill',
                'awb',
                'airport of departure',
                'airport of destination',
                'flight',
                'airline',
                'air freight'
            ],
            'loose_cargo': [
                'loose cargo',
                'break bulk',
                'general cargo',
                'bulk cargo',
                'no container',
                'packages',
                'pieces'
            ]
        }

    def extract_container_info(self, text: str, container_numbers: List[str]) -> ContainerInfo:
        """Extract container types and count from text"""
        text_lower = text.lower()
        detected_types = []
        confidence = 0.0
        
        # Count containers
        container_count = len(container_numbers) if container_numbers else 0
        
        # If no container numbers but we have container type info, try to extract count from text
        if container_count == 0:
            # Look for patterns like "TWO (40'HQ) CONTAINERS" or "2X40'HQ"
            count_patterns = [
                (r'two\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?\s*containers?', 2),
                (r'2\s*[Xx]\s*40\s*[\'`]\s*[Hh][Qq]', 2),
                (r'three\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?\s*containers?', 3),
                (r'3\s*[Xx]\s*40\s*[\'`]\s*[Hh][Qq]', 3),
                (r'(\d+)\s*[Xx]\s*40\s*[\'`]\s*[Hh][Qq]', None),  # Will extract number from group
                (r'total\s*:\s*two\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?\s*containers?', 2),
                (r'total\s*:\s*(\d+)\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?\s*containers?', None)
            ]
            
            for pattern, default_count in count_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    if default_count is None and isinstance(matches[0], tuple):
                        # Extract number from group
                        container_count = int(matches[0][0])
                    elif default_count is not None:
                        # Use the default count
                        container_count = default_count
                    print(f"[DEBUG] Found container count from pattern '{pattern}': {container_count}")
                    break
        
        # Detect container types
        for container_type, patterns in self.container_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    if container_type not in detected_types:  # Avoid duplicates
                        detected_types.append(container_type)
                        confidence += 0.4  # Boost confidence for each type found
                    break
        
        # Special handling for "2X40'HQ" format
        if not detected_types:
            # Look for specific patterns like "2X40'HQ" or "TWO (40'HQ)"
            hq_patterns = [
                r'2\s*[Xx]\s*40\s*[\'`]\s*[Hh][Qq]',
                r'two\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?',
                r'2\s*[Xx]\s*40\s*[\'`]\s*[Hh][Cc]',
                r'two\s*\(?\s*40\s*[\'`]\s*[Hh][Cc]\s*\)?',
                r'total\s*:\s*two\s*\(?\s*40\s*[\'`]\s*[Hh][Qq]\s*\)?\s*containers?',
                r'40\s*[\'`]\s*[Hh][Qq]',
                r'40\s*[\'`]\s*[Hh][Cc]'
            ]
            for pattern in hq_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    detected_types.append('40ft_hc')
                    confidence += 0.5
                    print(f"[DEBUG] Found 40ft_hc container type from pattern: {pattern}")
                    break
        
        # If no specific types detected, make educated guess based on container count
        if not detected_types and container_count > 0:
            if container_count == 1:
                detected_types = ['20ft']  # Most common single container
                confidence = 0.5
            else:
                detected_types = ['40ft']  # Multiple containers often 40ft
                confidence = 0.6
        
        # Normalize confidence
        confidence = min(confidence, 1.0)
        
        return ContainerInfo(
            container_numbers=container_numbers,
            container_types=detected_types,
            container_count=container_count,
            confidence=confidence
        )

    def extract_weight_info(self, text: str) -> WeightInfo:
        """Extract weight information from text"""
        text_lower = text.lower()
        total_weight_kg = 0.0
        weight_unit = 'kg'
        confidence = 0.0
        
        # Look for weight patterns
        for pattern in self.weight_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        # Handle different match formats
                        if isinstance(match, tuple):
                            weight_str, unit = match
                        else:
                            weight_str = match
                            unit = 'kg'  # Default to kg
                        
                        weight = float(weight_str)
                        if unit.lower() in ['lbs', 'pounds', 'lb']:
                            weight_kg = weight * 0.453592  # Convert lbs to kg
                            weight_unit = 'lbs'
                        elif unit.lower() == 'k':
                            weight_kg = weight  # "K" in AWBs typically means kg
                            weight_unit = 'kg'
                        else:
                            weight_kg = weight
                            weight_unit = 'kg'
                        
                        # Use the largest weight found (likely total weight)
                        if weight_kg > total_weight_kg:
                            total_weight_kg = weight_kg
                            confidence += 0.4
                    except (ValueError, TypeError):
                        continue
        
        # Special handling for BOL format like "20486.80 kgs"
        if total_weight_kg == 0.0:
            # Look for specific BOL weight patterns
            weight_patterns = [
                r'(\d+(?:\.\d+)?)\s*kgs?\b',
                r'(\d+(?:\.\d+)?)\s*kg\s*/\s*\d+(?:\.\d+)?\s*cbm',
                r'(\d+(?:\.\d+)?)\s*kgs?\s*/\s*\d+(?:\.\d+)?\s*cbm',
                r'gross\s*weight[:\s]*(\d+(?:\.\d+)?)\s*kgs?',
                r'total\s*weight[:\s]*(\d+(?:\.\d+)?)\s*kgs?'
            ]
            
            all_weights = []
            for pattern in weight_patterns:
                weight_matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if weight_matches:
                    try:
                        weights = [float(w) for w in weight_matches]
                        all_weights.extend(weights)
                    except ValueError:
                        continue
            
            if all_weights:
                # Use the largest weight found (likely total weight)
                total_weight_kg = max(all_weights)
                confidence = 0.7
                
                # If we found multiple weights, boost confidence
                if len(all_weights) > 1:
                    confidence = 0.8
        
        return WeightInfo(
            total_weight_kg=total_weight_kg,
            weight_unit=weight_unit,
            confidence=min(confidence, 1.0)
        )

    def extract_bl_number_legacy(self, text: str) -> str:
        """Extract BL number using original legacy logic for better accuracy"""
        lines = text.splitlines()
        candidate_labels = ['Waybill No.', 'Document No.', 'Bill of Lading Number', 'B/L No.', 'BL NO', 'B/L NO']
        
        for i, line in enumerate(lines):
            for label in candidate_labels:
                if label.lower() in line.lower():
                    match = re.search(r'[:\s\-]*([A-Z0-9\-]{8,})', line)
                    if match:
                        candidate = match.group(1).strip()
                        if candidate.upper() != 'LADING':
                            return candidate
                    if i + 1 < len(lines):
                        match2 = re.search(r'\b[A-Z0-9\-]{8,}\b', lines[i + 1])
                        if match2 and match2.group(0).upper() != 'LADING':
                            return match2.group(0)
        
        # Fallback: look for common BL number patterns
        match = re.search(r'\b\d{10,}\b|\b[A-Z]{3}\d{6,}\b|\b\d{3}-\d{7,8}\b', text)
        if match and match.group(0).upper() != 'LADING':
            return match.group(0)
        
        return ""

    def extract_ports_legacy(self, text: str) -> Dict[str, str]:
        """Extract ports using original legacy logic for better accuracy"""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        def find_port_after_keyword(keywords: List[str], default: str = "") -> str:
            for i, line in enumerate(lines):
                for k in keywords:
                    if k.lower() in line.lower():
                        # Look for port name in the next few lines
                        for j in range(i + 1, min(i + 4, len(lines))):
                            next_line = lines[j]
                            if next_line:
                                # Clean up the port name - remove form labels and numbers
                                port = next_line.split(',')[0].strip()
                                # Remove common form labels and numbers
                                port = re.sub(r'^\d+\.\s*', '', port)  # Remove "15. " or "16. "
                                port = re.sub(r'^\d+\s*', '', port)   # Remove "15 " or "16 "
                                port = re.sub(r'^[A-Z\s]+\s*$', '', port)  # Remove all-caps labels
                                port = port.strip()
                                
                                # Validate that it's a real port name (not empty, not too long, contains letters)
                                if port and len(port) > 2 and len(port) < 50 and any(c.isalpha() for c in port):
                                    # Additional check: make sure it's not a form label
                                    form_labels = [
                                        'LOADING', 'PIER', 'TERMINAL', 'PLACE', 'DELIVERY', 'CARRIER',
                                        'CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY', 'AIR', 'FREIGHT',
                                        'OCEAN', 'CARGO', 'SHIPMENT', 'TYPE', 'MOVE', 'CY', 'CFS'
                                    ]
                                    if not any(label in port.upper() for label in form_labels):
                                        # Additional check for patterns like "a. CONTAINERIZED"
                                        if not re.match(r'^[a-z]\.\s*[A-Z]', port, re.IGNORECASE):
                                            return port
            return default
        
        # First try the original method
        port_of_loading = find_port_after_keyword(['port of loading', 'port of export', 'place of receipt'])
        port_of_discharge = find_port_after_keyword(['port of discharge', 'place of delivery', 'foreign port of unloading'])
        
        # If we didn't find ports, try a more direct approach by looking for common port patterns
        if not port_of_loading or not port_of_discharge:
            # Look for port names that appear in the document
            # Common port patterns: YANTIAN, SHANGHAI, HONG KONG, LARGOS, NEW YORK, etc.
            port_patterns = [
                r'\b(YANTIAN|SHANGHAI|HONG KONG|LARGOS|NEW YORK|NIGERIA|HUNGARY|JAPAN|FRANCE)\b',
                r'\b([A-Z]{3,15})\b'  # General pattern for port names
            ]
            
            # Also look for specific port patterns in the document
            specific_port_patterns = [
                r'FOREIGN\s+PORT\s+OF\s+UNLOADING[:\s]*([A-Z\s]+)',
                r'PLACE\s+OF\s+DELIVERY[:\s]*([A-Z\s]+)',
                r'PORT\s+OF\s+DISCHARGE[:\s]*([A-Z\s]+)',
            ]
            
            for pattern in specific_port_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            port_candidate = match[0].strip()
                        else:
                            port_candidate = match.strip()
                        
                        # Clean up the port candidate
                        port_candidate = re.sub(r'\s+', ' ', port_candidate)
                        port_candidate = port_candidate.strip()
                        
                        # Filter out form labels
                        form_labels = ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY', 'AIR', 'FREIGHT', 'OCEAN', 'CARGO']
                        if not any(label in port_candidate.upper() for label in form_labels):
                            if not port_of_discharge and len(port_candidate) > 2:
                                port_of_discharge = port_candidate
                                print(f"[DEBUG] Found port of discharge from pattern '{pattern}': '{port_candidate}'")
                                break
            
            all_ports = []
            for pattern in port_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        all_ports.extend(match)
                    else:
                        all_ports.append(match)
            
            # Remove duplicates and filter out common non-port words
            unique_ports = list(set([p.upper() for p in all_ports if p]))
            non_port_words = ['BILL', 'LADING', 'FREIGHT', 'BROKERS', 'GLOBAL', 'SERVICES', 'DEAN', 'WAREHOUSE', 'SVC', 'BRUNSWICK', 'AVENUE', 'ROCKAWAY', 'KILVERT', 'STREET', 'WARWICK', 'BARBOSA', 'HUANG', 'ZHONGSHAN', 'TORCH', 'DEVELOPMENT', 'ZONE', 'GUANGDONG', 'PROVINCE', 'CHINA', 'PERFECT', 'TECHNOLOGIES', 'VALIANT', 'INDUSTRIAL', 'CENTRE', 'SHATIN', 'JETHING', 'INTERNATIONAL', 'SMART', 'FAMOUS', 'SOLEX', 'HAYWARD', 'INDUSTRIES', 'RAY', 'TOP', 'WONG', 'SO', 'FUN', 'NIGERIA', 'TIMON', 'OOCL', 'BERLIN', 'CY', 'YES', 'NO', 'SHIPPING', 'MARKS', 'SHIPPER', 'LOAD', 'COUNT', 'COUNTRY', 'ORIGIN', 'CTNS', 'PLTS', 'CONTR', 'PO', 'SEAL', 'ENCL', 'AQR', 'XFRMR', 'WHT', 'PUR', 'TURN', 'KEY', 'TROL', 'G1', 'REV', 'KGS', 'CBM', 'QTY', 'EACH', 'FREIGHT', 'COLLECT', 'TOTAL', 'CONTAINERS', 'ONLY', 'SHIPMENT', 'CONTAINS', 'WOOD', 'PACKING', 'MATERIALS', 'SHIPPED', 'BOARD', 'THESE', 'COMMODITIES', 'TECHNOLOGY', 'SOFTWARE', 'EXPORTED', 'FORM', 'ACCORDANCE', 'EXPORT', 'ADMINSTRATION', 'REGULATIONS', 'DIVERSION', 'CONTRARY', 'PROHIBITED', 'RATES', 'CHARGES', 'WEIGHTS', 'MEASUREMENTS', 'RECEIVED', 'CARRIER', 'SHIPMENT', 'OCEAN', 'VESSEL', 'BETWEEN', 'SUBJECT', 'CORRECTION', 'PREPAID', 'COLLECT', 'CARRIAGE', 'DELIVERY', 'WHERE', 'STATED', 'ABOVE', 'GOODS', 'SPECIFIED', 'APPARENT', 'ORDER', 'CONDITION', 'UNLESS', 'OTHERWISE', 'DELIVERED', 'MENTIONED', 'EXCEPTIONS', 'LIMITATIONS', 'AGREE', 'ACCEPTING', 'WITNESS', 'WHEREOF', 'ORIGINAL', 'SIGNED', 'OTHERWISE', 'ACCOMPLISHED', 'VOID', 'DATED', 'AGENT', 'MASTER', 'EXPORTER', 'PRINCIPAL', 'SELLER', 'LICENSEE', 'ADDRESS', 'INCLUDING', 'ZIP', 'CODE', 'DISCHAGE', 'ARRAGEMENT', 'PROCUREMENT', 'RECEIPT', 'CONDITIONS', 'LIBERTIES', 'REVESE', 'SIDE', 'HEREOF', 'CONSIGNEE', 'MO', 'DAY', 'YEAR', 'LADING', 'ERIZED', 'VESSEL', 'MEASUREMENT', 'PACKAGES', 'KILOS', 'DESCRIPTION', 'COMMODITIES', 'SCHEDULE', 'DETAIL', 'GROSS', 'WEIGHT', 'MEAS', 'MARKS', 'NUMBERS', 'NUMBER', 'TYPE', 'MOVE', 'CONTAIN', 'CONTAINERIZED', 'PRE', 'CARRIAGE', 'EXPORTING', 'FOREIGN', 'UNLOADING', 'DOMESTIC', 'ROUTING', 'INSTRUCTIONS', 'NOTIFY', 'PARTY', 'INTERMEDIATE', 'FORWARDING', 'REFERENCES', 'POINT', 'ORIGIN', 'FTZ', 'ZIP', 'CODE']
            
            filtered_ports = [p for p in unique_ports if p not in non_port_words and len(p) >= 3]
            
            # If we found ports, assign them based on position in document
            if filtered_ports:
                # Usually the first port mentioned is loading, second is discharge
                if len(filtered_ports) >= 2:
                    if not port_of_loading:
                        port_of_loading = filtered_ports[0]
                    if not port_of_discharge:
                        port_of_discharge = filtered_ports[1]
                elif len(filtered_ports) == 1:
                    if not port_of_loading:
                        port_of_loading = filtered_ports[0]
        
        # Override for CMA CGM
        if 'CMA CGM' in text.upper():
            port_match = re.search(r'PORT OF LOADING\s*[\n:]?\s*(.+)', text, re.IGNORECASE)
            if port_match:
                possible_port = port_match.group(1).strip()
                if "FREIGHT" not in possible_port.upper() and len(possible_port) <= 30:
                    port_of_loading = possible_port
        
        return {
            'port_of_loading': port_of_loading,
            'port_of_discharge': port_of_discharge
        }

    def classify_shipment_type(self, text: str, document_type: str) -> ShipmentInfo:
        """Classify shipment type based on document content"""
        text_lower = text.lower()
        scores = {'ocean': 0, 'air': 0, 'loose_cargo': 0}
        
        # Score based on indicators
        for shipment_type, indicators in self.shipment_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    scores[shipment_type] += 1
        
        # Boost score based on document type
        if document_type.upper() == 'BOL':
            scores['ocean'] += 3
        elif document_type.upper() == 'AWB':
            scores['air'] += 3
        
        # Determine shipment type
        shipment_type = max(scores, key=scores.get)
        max_score = scores[shipment_type]
        total_indicators = sum(len(indicators) for indicators in self.shipment_indicators.values())
        confidence = min(max_score / total_indicators, 1.0)
        
        return ShipmentInfo(
            shipment_type=shipment_type,
            document_type=document_type,
            confidence=confidence
        )

    def extract_company_name_only(self, text: str) -> str:
        """Extract only the company name from a string that may contain address information"""
        if not text or not isinstance(text, str):
            return text
        
        # Handle dict strings first - extract company_name if present
        if "'company_name':" in text:
            match = re.search(r"'company_name':\s*'([^']+)'", text)
            if match:
                company_name = match.group(1)
                print(f"[DEBUG] extract_company_name_only: '{text}' -> '{company_name}' (from dict)")
                return company_name
        
        # Common patterns to identify where company name ends and address begins
        address_indicators = [
            r'\s+C/O\s+',  # "C/O" (care of)
            r'\s+ATTN:\s*',  # "ATTN:" (attention)
            r'\s+TEL:\s*',  # "TEL:" (telephone)
            r'\s+FAX:\s*',  # "FAX:" (fax)
            r'\s+PHONE:\s*',  # "PHONE:"
            r'\s+EMAIL:\s*',  # "EMAIL:"
            r'\s+WEB:\s*',  # "WEB:"
            r'\s+WWW\.',  # "WWW."
            r'\s+\d{3,4}\s*[-.]?\s*\d{3,4}\s*[-.]?\s*\d{4}',  # Phone numbers
            r'\s+\d+\s+[A-Z\s]+(?:STREET|ST|AVENUE|AVE|ROAD|RD|BOULEVARD|BLVD|DRIVE|DR)',  # Street addresses
            r'\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?',  # ZIP codes
            r'\s+[A-Z\s]+,\s*[A-Z]{2}\s+\d{5}',  # "CITY, STATE ZIP"
            r'\s+[A-Z\s]+,\s*[A-Z\s]+,\s*[A-Z]{2}',  # "CITY, STATE"
            r'\s+[A-Z\s]+,\s*[A-Z]{2}',  # "CITY, STATE"
            r'\s+[A-Z]{2}\s+\d{5}',  # "STATE ZIP"
        ]
        
        # Find the earliest address indicator
        earliest_pos = len(text)
        for pattern in address_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.start() < earliest_pos:
                earliest_pos = match.start()
        
        # If we found an address indicator, cut the text there
        if earliest_pos < len(text):
            company_name = text[:earliest_pos].strip()
        else:
            company_name = text.strip()
        
        # Clean up common suffixes and extra whitespace
        company_name = re.sub(r'\s+', ' ', company_name)  # Normalize whitespace
        company_name = company_name.strip()
        
        # Remove trailing commas, periods, and other punctuation
        company_name = re.sub(r'[,\s\.]+$', '', company_name)
        
        print(f"[DEBUG] extract_company_name_only: '{text}' -> '{company_name}'")
        
        return company_name

    def extract_consignee_from_raw_text(self, text: str) -> str:
        """Extract consignee from raw text, prioritizing CONSIGNED TO over NOTIFY PARTY"""
        if not text:
            return ""
        
        # Look for CONSIGNED TO section first (this is the primary consignee)
        consignee_patterns = [
            r'3\.\s*CONSIGNED\s+TO[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)(?:\s|$)',
            r'CONSIGNED\s+TO[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)(?:\s|$)',
            r'CONSIGNEE[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)(?:\s|$)',
        ]
        
        for pattern in consignee_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                consignee = matches[0].strip()
                # Clean up the consignee name
                consignee = re.sub(r'\s+', ' ', consignee)  # Normalize whitespace
                consignee = consignee.strip()
                
                # Additional cleanup - remove any trailing text that looks like address
                # Stop at common address indicators
                address_indicators = [
                    r'\s+C/O\s+',
                    r'\s+ATTN:\s*',
                    r'\s+TEL:\s*',
                    r'\s+FAX:\s*',
                    r'\s+\d+\s+[A-Z\s]+(?:STREET|ST|AVENUE|AVE|ROAD|RD)',
                    r'\s+[A-Z]{2}\s+\d{5}',
                    r'\s+C\s*$',  # Remove trailing "C" (from C/O)
                    r'\s+[A-Z]\s*$',  # Remove trailing single letters
                ]
                
                earliest_pos = len(consignee)
                for addr_pattern in address_indicators:
                    match = re.search(addr_pattern, consignee, re.IGNORECASE)
                    if match and match.start() < earliest_pos:
                        earliest_pos = match.start()
                
                if earliest_pos < len(consignee):
                    consignee = consignee[:earliest_pos].strip()
                
                # Remove trailing single letters (like "C" from "C/O")
                consignee = re.sub(r'\s+[A-Z]\s*$', '', consignee)
                consignee = consignee.strip()
                
                if len(consignee) > 3:  # Valid consignee name
                    print(f"[DEBUG] Found consignee from pattern '{pattern}': '{consignee}'")
                    return consignee
        
        return ""

    def extract_ports_from_raw_text(self, text: str) -> Dict[str, str]:
        """Extract ports from raw text using specific patterns"""
        if not text:
            return {"port_of_loading": "", "port_of_discharge": ""}
        
        port_of_loading = ""
        port_of_discharge = ""
        
        # Look for specific port patterns
        port_patterns = [
            # Port of Loading patterns
            (r'PORT\s+OF\s+LOADING[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_loading'),
            (r'PORT\s+OF\s+EXPORT[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_loading'),
            (r'15\.\s*PORT\s+OF\s+LOADING[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_loading'),
            
            # Port of Discharge patterns
            (r'FOREIGN\s+PORT\s+OF\s+UNLOADING[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
            (r'PLACE\s+OF\s+DELIVERY\s+BY\s+ON-CARRIER[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
            (r'PORT\s+OF\s+DISCHARGE[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
            (r'16\.\s*FOREIGN\s+PORT\s+OF\s+UNLOADING[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
            (r'17\.\s*PLACE\s+OF\s+DELIVERY\s+BY\s+ON-CARRIER[:\s]*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
        ]
        
        for pattern, port_type in port_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        port_candidate = match[0].strip()
                    else:
                        port_candidate = match.strip()
                    
                    # Clean up the port candidate
                    port_candidate = re.sub(r'\s+', ' ', port_candidate)
                    port_candidate = port_candidate.strip()
                    
                    # Filter out form labels and invalid patterns
                    form_labels = [
                        'CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY', 'AIR', 'FREIGHT', 
                        'OCEAN', 'CARGO', 'SHIPMENT', 'TYPE', 'MOVE', 'CY', 'CFS',
                        'LOADING', 'PIER', 'TERMINAL', 'PLACE', 'DELIVERY', 'CARRIER',
                        'BY', 'ON', 'AND', 'VESSEL', 'AIR'
                    ]
                    
                    # Check for patterns like "a. CONTAINERIZED"
                    if (not any(label in port_candidate.upper() for label in form_labels) and
                        not re.match(r'^[a-z]\.\s*[A-Z]', port_candidate, re.IGNORECASE) and
                        len(port_candidate) > 2 and len(port_candidate) < 30):
                        
                        if port_type == 'port_of_loading' and not port_of_loading:
                            port_of_loading = port_candidate
                            print(f"[DEBUG] Found port of loading from pattern '{pattern}': '{port_candidate}'")
                        elif port_type == 'port_of_discharge' and not port_of_discharge:
                            port_of_discharge = port_candidate
                            print(f"[DEBUG] Found port of discharge from pattern '{pattern}': '{port_candidate}'")
        
        # If we still don't have ports, try more specific patterns
        if not port_of_loading or not port_of_discharge:
            # Look for patterns like "15. PORT OF LOADING/EXPORT: HONG KONG"
            specific_patterns = [
                (r'15\.\s*PORT\s+OF\s+LOADING[^:]*:\s*([A-Z\s]+?)(?:\s|$)', 'port_of_loading'),
                (r'16\.\s*FOREIGN\s+PORT\s+OF\s+UNLOADING[^:]*:\s*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
                (r'17\.\s*PLACE\s+OF\s+DELIVERY[^:]*:\s*([A-Z\s]+?)(?:\s|$)', 'port_of_discharge'),
            ]
            
            for pattern, port_type in specific_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    port_candidate = matches[0].strip()
                    if len(port_candidate) > 2 and len(port_candidate) < 30:
                        if port_type == 'port_of_loading' and not port_of_loading:
                            port_of_loading = port_candidate
                            print(f"[DEBUG] Found port of loading from specific pattern '{pattern}': '{port_candidate}'")
                        elif port_type == 'port_of_discharge' and not port_of_discharge:
                            port_of_discharge = port_candidate
                            print(f"[DEBUG] Found port of discharge from specific pattern '{pattern}': '{port_candidate}'")
        
        return {
            "port_of_loading": port_of_loading,
            "port_of_discharge": port_of_discharge
        }

    def calculate_fees(self, container_info: ContainerInfo, weight_info: WeightInfo, 
                      shipment_info: ShipmentInfo) -> Dict:
        """Calculate fees based on extracted information"""
        from config import get_db_conn
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get pricing configuration
        cursor.execute("""
            SELECT ctn_fee_per_unit, service_fee_per_unit, unit_type, minimum_charge
            FROM pricing_config 
            WHERE shipment_type = %s 
                AND (container_type = %s OR container_type IS NULL)
                AND is_active = TRUE
            ORDER BY container_type NULLS LAST
            LIMIT 1
        """, (shipment_info.shipment_type, 
              container_info.container_types[0] if container_info.container_types else None))
        
        pricing = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not pricing:
            # Fallback to default pricing
            ctn_fee_per_unit = 100.0
            service_fee_per_unit = 100.0
            unit_type = 'container'
            minimum_charge = 200.0
        else:
            # Convert Decimal objects to float for JSON serialization
            ctn_fee_per_unit = float(pricing[0]) if pricing[0] else 100.0
            service_fee_per_unit = float(pricing[1]) if pricing[1] else 100.0
            unit_type = pricing[2] if pricing[2] else 'container'
            minimum_charge = float(pricing[3]) if pricing[3] else 200.0
        
        # Calculate fees based on unit type
        if unit_type == 'container':
            ctn_fee = ctn_fee_per_unit * container_info.container_count
            service_fee = service_fee_per_unit * container_info.container_count
        elif unit_type == 'kg':
            ctn_fee = ctn_fee_per_unit * weight_info.total_weight_kg
            service_fee = service_fee_per_unit * weight_info.total_weight_kg
        else:
            ctn_fee = ctn_fee_per_unit
            service_fee = service_fee_per_unit
        
        # Apply minimum charge
        total_fee = ctn_fee + service_fee
        if total_fee < minimum_charge:
            # Distribute minimum charge proportionally
            ratio = minimum_charge / total_fee if total_fee > 0 else 1
            ctn_fee *= ratio
            service_fee *= ratio
        
        return {
            'ctn_fee': round(ctn_fee, 2),
            'service_fee': round(service_fee, 2),
            'total_fee': round(ctn_fee + service_fee, 2),
            'pricing_method': unit_type,
            'calculation_details': {
                'container_count': container_info.container_count,
                'container_types': container_info.container_types,
                'weight_kg': float(weight_info.total_weight_kg) if weight_info.total_weight_kg else None,
                'weight_unit': weight_info.weight_unit,
                'shipment_type': shipment_info.shipment_type,
                'ctn_fee_per_unit': float(ctn_fee_per_unit) if ctn_fee_per_unit else None,
                'service_fee_per_unit': float(service_fee_per_unit) if service_fee_per_unit else None,
                'minimum_charge': float(minimum_charge) if minimum_charge else None
            }
        }

    def process_document(self, pdf_path: str, use_openai: bool = True) -> Dict:
        """Process document with enhanced OCR and fee calculation"""
        try:
            # Extract basic fields using existing OCR
            if use_openai:
                basic_fields = extract_fields_openai(pdf_path)
            else:
                # Try Google Vision first, fallback to OpenAI
                try:
                    if GOOGLE_VISION_AVAILABLE and extract_fields_legacy:
                        basic_fields = extract_fields_legacy(pdf_path)
                        print("[DEBUG] Using Google Vision extraction")
                    else:
                        raise Exception("Google Vision not available")
                except Exception as e:
                    print(f"[DEBUG] Google Vision failed: {e}, falling back to OpenAI")
                    basic_fields = extract_fields_openai(pdf_path)
            
            text = basic_fields.get('raw_text', '')
            container_numbers_raw = basic_fields.get('container_numbers', [])
            document_type = basic_fields.get('document_type', 'BOL')
            
            # Parse container numbers - handle both string and list formats
            container_numbers = []
            if isinstance(container_numbers_raw, str):
                # Handle special cases first
                if container_numbers_raw == "2X40'HQ" or container_numbers_raw.startswith("2X") or container_numbers_raw.startswith("3X"):
                    # This is a container type description, not container numbers
                    # Try to extract actual container numbers from the raw text
                    # Look for patterns like "CONTR # OOCU7645789" or "CONTR # TGBU8072614"
                    container_patterns = [
                        r'CONTR\s*#\s*([A-Z]{4}\d{7})',
                        r'CONTR\s*#\s*([A-Z0-9]{11})',
                        r'CONTR\s*#\s*([A-Z0-9]+)',
                    ]
                    
                    for pattern in container_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            container_numbers = matches
                            break
                    
                    # If still no containers found, try broader pattern
                    if not container_numbers:
                        # Look for any 11-character alphanumeric strings that might be container numbers
                        potential_containers = re.findall(r'\b[A-Z]{4}\d{7}\b', text)
                        if potential_containers:
                            container_numbers = potential_containers
                elif '/' in container_numbers_raw:
                    # Handle container numbers like "KEIS2374724/20'" or "EMCU1041367, EMCU1059030"
                    parts = [p.strip() for p in container_numbers_raw.split(',')]
                    for part in parts:
                        if '/' in part:
                            # Extract container number before the slash
                            container_num = part.split('/')[0].strip()
                            if len(container_num) >= 4:  # Valid container number
                                container_numbers.append(container_num)
                        else:
                            if len(part) >= 4:  # Valid container number
                                container_numbers.append(part)
                else:
                    # Simple comma-separated list - but be more careful about splitting
                    # Look for actual container number patterns (4+ alphanumeric characters)
                    potential_containers = re.findall(r'\b[A-Z]{4}\d{7}\b', container_numbers_raw)
                    if potential_containers:
                        container_numbers = potential_containers
                    else:
                        # Fallback to comma splitting but filter properly
                        parts = [p.strip() for p in container_numbers_raw.split(',')]
                        container_numbers = [p for p in parts if len(p) >= 4 and re.match(r'^[A-Z0-9]+$', p)]
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
            else:
                container_numbers = []
            
            # If no container numbers found from OCR, try to extract from raw text
            if not container_numbers:
                print("[DEBUG] No container numbers from OCR, trying to extract from raw text")
                # Look for container number patterns in the raw text
                container_patterns = [
                    r'\b[A-Z]{4}\d{7}\b',  # Standard container format
                    r'CONTR\s*#\s*([A-Z]{4}\d{7})',
                    r'CONTR\s*#\s*([A-Z0-9]{11})',
                    r'CONTR\s*#\s*([A-Z0-9]+)',
                ]
                
                for pattern in container_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        if isinstance(matches[0], tuple):
                            # Extract from group
                            container_numbers = [m[0] for m in matches if m[0]]
                        else:
                            container_numbers = matches
                        print(f"[DEBUG] Found {len(container_numbers)} container numbers from raw text: {container_numbers}")
                        break
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
            else:
                container_numbers = []
            
            # Enhanced extraction
            container_info = self.extract_container_info(text, container_numbers)
            weight_info = self.extract_weight_info(text)
            shipment_info = self.classify_shipment_type(text, document_type)
            
            # Improve BL number extraction using legacy logic
            improved_bl_number = self.extract_bl_number_legacy(text)
            if improved_bl_number:
                basic_fields['bl_number'] = improved_bl_number
                print(f"[DEBUG] Legacy BL number extraction: {improved_bl_number}")
            else:
                print(f"[DEBUG] Legacy BL number extraction failed, keeping: {basic_fields.get('bl_number', 'N/A')}")
            
            # Improve port extraction using legacy logic
            improved_ports = self.extract_ports_legacy(text)
            
            # Only override if the original OCR didn't extract valid ports
            if not basic_fields.get('port_of_loading') or basic_fields.get('port_of_loading') == '':
                if improved_ports.get('port_of_loading'):
                    basic_fields['port_of_loading'] = improved_ports['port_of_loading']
                    print(f"[DEBUG] Legacy port of loading: {improved_ports['port_of_loading']}")
            
            if not basic_fields.get('port_of_discharge') or basic_fields.get('port_of_discharge') == '':
                if improved_ports.get('port_of_discharge'):
                    basic_fields['port_of_discharge'] = improved_ports['port_of_discharge']
                    print(f"[DEBUG] Legacy port of discharge: {improved_ports['port_of_discharge']}")
            
            # If we still don't have ports, try the legacy extraction
            if (not basic_fields.get('port_of_loading') or basic_fields.get('port_of_loading') == '') and improved_ports.get('port_of_loading'):
                basic_fields['port_of_loading'] = improved_ports['port_of_loading']
                print(f"[DEBUG] Using legacy port of loading: {improved_ports['port_of_loading']}")
                
            if (not basic_fields.get('port_of_discharge') or basic_fields.get('port_of_discharge') == '') and improved_ports.get('port_of_discharge'):
                basic_fields['port_of_discharge'] = improved_ports['port_of_discharge']
                print(f"[DEBUG] Using legacy port of discharge: {improved_ports['port_of_discharge']}")
            
            # If we still don't have ports or they contain form labels, try raw text extraction
            if (not basic_fields.get('port_of_loading') or 
                basic_fields.get('port_of_loading') == '' or
                any(label in basic_fields.get('port_of_loading', '').upper() for label in ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY'])):
                
                raw_ports = self.extract_ports_from_raw_text(text)
                if raw_ports.get('port_of_loading'):
                    basic_fields['port_of_loading'] = raw_ports['port_of_loading']
                    print(f"[DEBUG] Using raw text port of loading: {raw_ports['port_of_loading']}")
            
            if (not basic_fields.get('port_of_discharge') or 
                basic_fields.get('port_of_discharge') == '' or
                any(label in basic_fields.get('port_of_discharge', '').upper() for label in ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY'])):
                
                raw_ports = self.extract_ports_from_raw_text(text)
                if raw_ports.get('port_of_discharge'):
                    basic_fields['port_of_discharge'] = raw_ports['port_of_discharge']
                    print(f"[DEBUG] Using raw text port of discharge: {raw_ports['port_of_discharge']}")
            
            # Improve flight/vessel extraction if missing
            if not basic_fields.get('flight_or_vessel') or basic_fields.get('flight_or_vessel') == '':
                # Look for vessel names in the raw text
                vessel_patterns = [
                    r'EXPORTING\s+CARRIER[:\s]*([A-Z0-9\s\.\-]+)',
                    r'VESSEL[:\s]*([A-Z0-9\s\.\-]+)',
                    r'CARRIER[:\s]*([A-Z0-9\s\.\-]+)',
                    r'([A-Z]{3,4}\s+[A-Z]+\s+v\.\d+[A-Z])',  # Pattern like "OOCL BERLIN v.041E"
                ]
                
                for pattern in vessel_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        vessel_name = matches[0].strip()
                        # Clean up the vessel name
                        vessel_name = re.sub(r'^\d+\.\s*', '', vessel_name)  # Remove section numbers
                        vessel_name = vessel_name.strip()
                        if len(vessel_name) > 3:  # Valid vessel name
                            basic_fields['flight_or_vessel'] = vessel_name
                            print(f"[DEBUG] Found vessel name from pattern '{pattern}': {vessel_name}")
                            break
                
            # Calculate fees
            fee_calculation = self.calculate_fees(container_info, weight_info, shipment_info)
            
            # Calculate overall confidence
            overall_confidence = (
                container_info.confidence * 0.4 +
                weight_info.confidence * 0.3 +
                shipment_info.confidence * 0.3
            )
            
            # Clean up consignee field to separate notify party information
            # Ensure consignee is a string, not a dict
            raw_consignee = basic_fields.get('consignee', '')
            if isinstance(raw_consignee, dict):
                print(f"[DEBUG] Consignee is a dict: {raw_consignee}")
                # If it's a dict, try to extract just the company name
                if 'company_name' in raw_consignee:
                    consignee = raw_consignee['company_name']
                else:
                    consignee = str(raw_consignee)
            else:
                consignee = str(raw_consignee) if raw_consignee else ''
            
            raw_notify_party = basic_fields.get('notify_party', '')
            if isinstance(raw_notify_party, dict):
                print(f"[DEBUG] Notify party is a dict: {raw_notify_party}")
                # If it's a dict, try to extract just the company name
                if 'company_name' in raw_notify_party:
                    notify_party = raw_notify_party['company_name']
                else:
                    notify_party = str(raw_notify_party)
            else:
                notify_party = str(raw_notify_party) if raw_notify_party else ''
            
            print(f"[DEBUG] Processed consignee: '{consignee}' (type: {type(consignee).__name__})")
            print(f"[DEBUG] Processed notify_party: '{notify_party}' (type: {type(notify_party).__name__})")
            
            # Clean up consignee to extract just the company name
            if consignee and isinstance(consignee, str):
                # Remove address information and keep only company name
                consignee = self.extract_company_name_only(consignee)
            
            # Clean up notify party to extract just the company name
            if notify_party and isinstance(notify_party, str):
                # Remove address information and keep only company name
                notify_party = self.extract_company_name_only(notify_party)
            
            # If consignee is still empty or seems wrong, try to extract from raw text
            if not consignee or consignee == notify_party:
                extracted_consignee = self.extract_consignee_from_raw_text(text)
                if extracted_consignee:
                    consignee = self.extract_company_name_only(extracted_consignee)
                    print(f"[DEBUG] Extracted consignee from raw text: '{extracted_consignee}' -> '{consignee}'")
            
            # If notify_party is not already extracted, try to separate it from consignee
            # But be more conservative - only process if consignee is very long or clearly contains multiple parties
            if not notify_party and consignee and isinstance(consignee, str) and len(consignee) > 100:
                # Only process very long consignee fields that likely contain multiple parties
                # Pattern 1: Multiple company names separated by common delimiters
                separators = ['\n', ';', '|', ' - ', ' / ', ' c/o ', ' ATTN:', 'ATTN:']
                
                for separator in separators:
                    if isinstance(consignee, str) and separator in consignee:
                        parts = consignee.split(separator)
                        if len(parts) >= 2:
                            # First part is usually consignee, second part might be notify party
                            potential_consignee = parts[0].strip()
                            potential_notify = parts[1].strip()
                            
                            # Validate that we have meaningful parts
                            if (len(potential_consignee) > 5 and len(potential_notify) > 5 and 
                                potential_consignee != potential_notify):
                                consignee = potential_consignee
                                notify_party = potential_notify
                                break
                
                # Pattern 2: Look for "SAME AS CONSIGNEE" or similar indicators
                if isinstance(consignee, str) and 'SAME AS CONSIGNEE' in consignee.upper():
                    # Remove the "SAME AS CONSIGNEE" part
                    consignee = consignee.replace('SAME AS CONSIGNEE', '').replace('SAME AS CONSIGNEE', '').strip()
                    # If consignee is now empty or too short, keep original
                    if len(consignee) < 5:
                        consignee = str(basic_fields.get('consignee', ''))
                
                # Pattern 3: Look for multiple addresses (indicated by multiple phone numbers or addresses)
                if isinstance(consignee, str) and (consignee.count('TEL:') > 1 or consignee.count('FAX:') > 1):
                    # Try to split on phone/fax indicators
                    phone_parts = consignee.split('TEL:')
                    if len(phone_parts) >= 3:  # At least 2 phone numbers
                        # First part is consignee, second part might be notify party
                        consignee = phone_parts[0].strip()
                        notify_party = 'TEL:'.join(phone_parts[1:]).strip()
            
            # Prepare enhanced result
            enhanced_fields = {
                # Original fields
                **basic_fields,
                
                # Update container_numbers based on shipment type - convert list to string
                'container_numbers': 'N/A' if shipment_info.shipment_type == 'air' else (', '.join(container_numbers) if isinstance(container_numbers, list) else str(container_numbers)),
                
                # Debug: Log container numbers for troubleshooting
                'debug_container_numbers': {
                    'raw_container_numbers': container_numbers,
                    'type': type(container_numbers).__name__,
                    'shipment_type': shipment_info.shipment_type,
                    'final_result': 'N/A' if shipment_info.shipment_type == 'air' else (', '.join(container_numbers) if isinstance(container_numbers, list) else str(container_numbers))
                },
                
                # Clean up consignee and add notify_party
                # Ensure consignee is never empty - fallback to original if processed version is empty
                'consignee': consignee if consignee and isinstance(consignee, str) and consignee.strip() else str(basic_fields.get('consignee', '')),
                'notify_party': notify_party,
                
                # Debug: Log consignee processing for troubleshooting
                'debug_consignee': {
                    'original_consignee': str(basic_fields.get('consignee', '')),
                    'final_consignee': str(consignee) if consignee else '',
                    'notify_party': str(notify_party) if notify_party else '',
                    'was_processed': str(consignee) != str(basic_fields.get('consignee', ''))
                },
                
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
            
            logger.info(f"Enhanced OCR completed with confidence: {overall_confidence:.2f}")
            return enhanced_fields
            
        except Exception as e:
            logger.error(f"Enhanced OCR processing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return basic fields if available, otherwise empty dict
            if 'basic_fields' in locals():
                return {
                    **basic_fields,
                    'error': str(e),
                    'ocr_confidence_score': 0.0,
                    'calculated_ctn_fee': 100.0,  # Fallback
                    'calculated_service_fee': 100.0  # Fallback
                }
            else:
                return {
                    'error': str(e),
                    'ocr_confidence_score': 0.0,
                    'calculated_ctn_fee': 100.0,  # Fallback
                    'calculated_service_fee': 100.0  # Fallback
                }

# Global instance
enhanced_ocr = EnhancedOCRProcessor()

def extract_fields_enhanced(pdf_path: str, use_openai: bool = True) -> Dict:
    """Enhanced field extraction with container and weight detection"""
    return enhanced_ocr.process_document(pdf_path, use_openai)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python enhanced_ocr_processor.py <pdf_path>")
        sys.exit(1)
    
    result = extract_fields_enhanced(sys.argv[1])
    print(json.dumps(result, indent=2)) 