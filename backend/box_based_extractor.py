#!/usr/bin/env python3
"""
Box-based OCR extraction system
Uses coordinates and field mapping instead of regex patterns
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

@dataclass
class FieldBox:
    """Defines a field's location and properties"""
    name: str
    x1: float  # Left coordinate (0-1)
    y1: float  # Top coordinate (0-1)
    x2: float  # Right coordinate (0-1)
    y2: float  # Bottom coordinate (0-1)
    field_type: str  # 'text', 'port', 'container', 'weight'
    keywords: List[str]  # Keywords to look for near this area
    fallback_keywords: List[str] = None  # Alternative keywords

@dataclass
class ExtractedField:
    """Result of field extraction"""
    name: str
    value: str
    confidence: float
    source: str  # 'box', 'keyword', 'fallback'

class BoxBasedExtractor:
    """Extracts data using box coordinates and field mapping"""
    
    def __init__(self):
        # Define standard BOL field locations (normalized coordinates 0-1)
        self.standard_fields = [
            # Shipper section (top left)
            FieldBox("shipper", 0.05, 0.15, 0.45, 0.25, "text", 
                    ["SHIPPER", "EXPORTER", "2."]),
            
            # Consignee section (top right)
            FieldBox("consignee", 0.55, 0.15, 0.95, 0.25, "text",
                    ["CONSIGNED TO", "CONSIGNEE", "3."]),
            
            # Notify Party section (below consignee)
            FieldBox("notify_party", 0.55, 0.30, 0.95, 0.40, "text",
                    ["NOTIFY PARTY", "4."]),
            
            # BL Number (top center)
            FieldBox("bl_number", 0.45, 0.05, 0.55, 0.10, "text",
                    ["B/L NUMBER", "6a."]),
            
            # Port of Loading (left side, middle)
            FieldBox("port_of_loading", 0.05, 0.45, 0.45, 0.50, "port",
                    ["PORT OF LOADING", "15."]),
            
            # Port of Discharge (right side, middle)
            FieldBox("port_of_discharge", 0.55, 0.45, 0.95, 0.50, "port",
                    ["FOREIGN PORT OF UNLOADING", "PLACE OF DELIVERY", "16.", "17."]),
            
            # Container Numbers (bottom left)
            FieldBox("container_numbers", 0.05, 0.70, 0.45, 0.80, "container",
                    ["CONTR #", "CONTAINER"]),
            
            # Flight/Vessel (bottom center)
            FieldBox("flight_or_vessel", 0.45, 0.60, 0.55, 0.65, "text",
                    ["EXPORTING CARRIER", "VESSEL", "14."]),
            
            # Product Description (bottom right)
            FieldBox("product_description", 0.55, 0.70, 0.95, 0.90, "text",
                    ["DESCRIPTION OF COMMODITIES", "20."]),
        ]
        
        # Alternative field layouts for different BOL formats
        self.alternative_layouts = {
            "cma_cgm": [
                FieldBox("shipper", 0.05, 0.10, 0.45, 0.20, "text", ["SHIPPER"]),
                FieldBox("consignee", 0.55, 0.10, 0.95, 0.20, "text", ["CONSIGNEE"]),
                FieldBox("port_of_loading", 0.05, 0.35, 0.45, 0.40, "port", ["PORT OF LOADING"]),
                FieldBox("port_of_discharge", 0.55, 0.35, 0.95, 0.40, "port", ["PORT OF DISCHARGE"]),
            ],
            "maersk": [
                FieldBox("shipper", 0.05, 0.12, 0.45, 0.22, "text", ["SHIPPER"]),
                FieldBox("consignee", 0.55, 0.12, 0.95, 0.22, "text", ["CONSIGNEE"]),
                FieldBox("port_of_loading", 0.05, 0.40, 0.45, 0.45, "port", ["PORT OF LOADING"]),
                FieldBox("port_of_discharge", 0.55, 0.40, 0.95, 0.45, "port", ["PORT OF DISCHARGE"]),
            ]
        }
    
    def detect_document_type(self, text: str) -> str:
        """Detect BOL format based on text content"""
        text_upper = text.upper()
        
        if "CMA CGM" in text_upper:
            return "cma_cgm"
        elif "MAERSK" in text_upper:
            return "maersk"
        elif "OOCL" in text_upper:
            return "oocl"
        else:
            return "standard"
    
    def extract_from_coordinates(self, text: str, boxes: List[FieldBox]) -> Dict[str, ExtractedField]:
        """Extract fields using coordinate-based approach"""
        results = {}
        
        # Split text into lines for coordinate analysis
        lines = text.split('\n')
        total_lines = len(lines)
        
        for box in boxes:
            # Calculate line ranges for this box
            start_line = int(box.y1 * total_lines)
            end_line = int(box.y2 * total_lines)
            
            # Extract text from the box area
            box_text = '\n'.join(lines[start_line:end_line])
            
            # Extract field value based on type
            if box.field_type == "port":
                value = self._extract_port_value(box_text, box.keywords)
            elif box.field_type == "container":
                value = self._extract_container_value(box_text, box.keywords)
            else:
                value = self._extract_text_value(box_text, box.keywords)
            
            results[box.name] = ExtractedField(
                name=box.name,
                value=value,
                confidence=0.8,  # Base confidence
                source="box"
            )
        
        return results
    
    def _extract_text_value(self, text: str, keywords: List[str]) -> str:
        """Extract text value from a box area"""
        # Look for keywords and extract text after them
        for keyword in keywords:
            pattern = rf'{re.escape(keyword)}[:\s]*([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = re.sub(r'\s+', ' ', value)
                return value
        
        # If no keyword found, return the first non-empty line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines[0] if lines else ""
    
    def _extract_port_value(self, text: str, keywords: List[str]) -> str:
        """Extract port value, filtering out form labels"""
        value = self._extract_text_value(text, keywords)
        
        # Filter out form labels
        form_labels = [
            'CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY', 'AIR', 'FREIGHT',
            'OCEAN', 'CARGO', 'SHIPMENT', 'TYPE', 'MOVE', 'CY', 'CFS',
            'LOADING', 'PIER', 'TERMINAL', 'PLACE', 'DELIVERY', 'CARRIER',
            'BY', 'ON', 'AND'
        ]
        
        if any(label in value.upper() for label in form_labels):
            return ""
        
        # Check for patterns like "a. CONTAINERIZED"
        if re.match(r'^[a-z]\.\s*[A-Z]', value, re.IGNORECASE):
            return ""
        
        return value
    
    def _extract_container_value(self, text: str, keywords: List[str]) -> str:
        """Extract container numbers"""
        # Look for container number patterns
        container_patterns = [
            r'\b[A-Z]{4}\d{7}\b',  # Standard format
            r'CONTR\s*#\s*([A-Z]{4}\d{7})',
        ]
        
        for pattern in container_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return ', '.join([m[0] for m in matches if m[0]])
                else:
                    return ', '.join(matches)
        
        return ""
    
    def extract_with_fallback(self, text: str) -> Dict[str, str]:
        """Extract fields with fallback to keyword-based extraction"""
        # Detect document type
        doc_type = self.detect_document_type(text)
        
        # Get appropriate field boxes
        if doc_type in self.alternative_layouts:
            boxes = self.alternative_layouts[doc_type]
        else:
            boxes = self.standard_fields
        
        # Extract using box coordinates
        box_results = self.extract_from_coordinates(text, boxes)
        
        # Convert to simple dict
        results = {}
        for field_name, field_data in box_results.items():
            results[field_name] = field_data.value
        
        # Fallback to keyword-based extraction for missing fields
        missing_fields = [box.name for box in boxes if not results.get(box.name)]
        
        for field_name in missing_fields:
            fallback_value = self._keyword_fallback_extraction(text, field_name)
            if fallback_value:
                results[field_name] = fallback_value
        
        return results
    
    def _keyword_fallback_extraction(self, text: str, field_name: str) -> str:
        """Fallback extraction using keywords when box extraction fails"""
        keyword_maps = {
            "shipper": ["SHIPPER", "EXPORTER", "2."],
            "consignee": ["CONSIGNED TO", "CONSIGNEE", "3."],
            "notify_party": ["NOTIFY PARTY", "4."],
            "bl_number": ["B/L NUMBER", "6a."],
            "port_of_loading": ["PORT OF LOADING", "15."],
            "port_of_discharge": ["FOREIGN PORT OF UNLOADING", "PLACE OF DELIVERY", "16.", "17."],
            "container_numbers": ["CONTR #", "CONTAINER"],
            "flight_or_vessel": ["EXPORTING CARRIER", "VESSEL", "14."],
            "product_description": ["DESCRIPTION OF COMMODITIES", "20."],
        }
        
        keywords = keyword_maps.get(field_name, [])
        
        for keyword in keywords:
            pattern = rf'{re.escape(keyword)}[:\s]*([^\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field_name == "port_of_discharge":
                    return self._extract_port_value(value, [])
                elif field_name == "container_numbers":
                    return self._extract_container_value(value, [])
                else:
                    return value
        
        return ""

def extract_fields_box_based(text: str) -> Dict[str, str]:
    """Main function to extract fields using box-based approach"""
    extractor = BoxBasedExtractor()
    return extractor.extract_with_fallback(text)

if __name__ == "__main__":
    # Test the box-based extractor
    test_text = """
    15. PORT OF LOADING/EXPORT: HONG KONG
    16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): NIGERIA
    17. PLACE OF DELIVERY BY ON-CARRIER: NIGERIA
    """
    
    results = extract_fields_box_based(test_text)
    print("Box-based extraction results:")
    for field, value in results.items():
        print(f"  {field}: {value}") 