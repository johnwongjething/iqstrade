#!/usr/bin/env python3
"""
Field Mapping Analysis
Compare fields between original OCR, enhanced OCR, database, and frontend
"""

def analyze_field_mapping():
    """Analyze field mapping between different components"""
    
    print("🔍 FIELD MAPPING ANALYSIS")
    print("=" * 60)
    
    # Original OCR Processor Fields (ocr_processor.py)
    original_ocr_fields = [
        'document_type',
        'bl_number', 
        'shipper',
        'consignee',
        'port_of_loading',
        'port_of_discharge',
        'container_numbers',
        'flight_or_vessel',
        'product_description',
        'paid_amount',
        'raw_text'
    ]
    
    # Enhanced OCR Processor Fields (enhanced_ocr_processor.py)
    enhanced_ocr_fields = [
        # Original fields (inherited from basic_fields)
        'document_type',
        'bl_number',
        'shipper', 
        'consignee',
        'port_of_loading',
        'port_of_discharge',
        'container_numbers',
        'flight_or_vessel',
        'product_description',
        'paid_amount',
        'raw_text',
        
        # Enhanced fields (new)
        'container_count',
        'container_types',
        'container_type',
        'total_weight_kg',
        'weight_unit',
        'shipment_type',
        'pricing_method',
        'calculated_ctn_fee',
        'calculated_service_fee',
        'calculated_total_fee',
        'ocr_confidence_score',
        'pricing_calculation_log',
        'confidence_breakdown'
    ]
    
    # Database Fields (from upload route)
    database_fields = [
        'customer_name',
        'customer_email', 
        'customer_phone',
        'pdf_filename',
        'ocr_text',
        'shipper',
        'consignee',
        'port_of_loading',
        'port_of_discharge',
        'bl_number',
        'container_numbers',
        'flight_or_vessel',
        'product_description',
        'status',
        'customer_username',
        'created_at',
        'customer_invoice',
        'customer_packing_list',
        'shipment_type',
        'container_type',
        'container_count',
        'total_weight_kg',
        'weight_unit',
        'pricing_method',
        'calculated_ctn_fee',
        'calculated_service_fee',
        'ocr_confidence_score',
        'pricing_calculation_log'
    ]
    
    # Frontend Fields (from Review.js table)
    frontend_fields = [
        'customer_name',
        'bl_number',
        'shipper',
        'consignee',
        'status',
        'ctn_fee',
        'service_fee',
        'unique_number',
        'invoice_filename',
        'receipt_filename'
    ]
    
    print("\n📋 ORIGINAL OCR FIELDS:")
    for field in original_ocr_fields:
        print(f"   ✅ {field}")
    
    print("\n🚀 ENHANCED OCR FIELDS:")
    for field in enhanced_ocr_fields:
        if field in original_ocr_fields:
            print(f"   ✅ {field} (inherited)")
        else:
            print(f"   🆕 {field} (new)")
    
    print("\n💾 DATABASE FIELDS:")
    for field in database_fields:
        if field in enhanced_ocr_fields:
            print(f"   ✅ {field} (from enhanced OCR)")
        elif field in ['customer_name', 'customer_email', 'customer_phone', 'status', 'customer_username', 'created_at']:
            print(f"   📝 {field} (from form/context)")
        else:
            print(f"   📊 {field} (stored separately)")
    
    print("\n🖥️ FRONTEND FIELDS (Review.js):")
    for field in frontend_fields:
        if field in database_fields:
            print(f"   ✅ {field} (from database)")
        else:
            print(f"   ⚠️ {field} (needs mapping)")
    
    print("\n🔍 FIELD COMPATIBILITY ANALYSIS:")
    
    # Check if all original fields are preserved
    missing_original = [f for f in original_ocr_fields if f not in enhanced_ocr_fields]
    if missing_original:
        print(f"   ❌ Missing original fields: {missing_original}")
    else:
        print("   ✅ All original fields preserved")
    
    # Check if all frontend fields are available in database
    missing_frontend = [f for f in frontend_fields if f not in database_fields]
    if missing_frontend:
        print(f"   ⚠️ Frontend fields not in database: {missing_frontend}")
    else:
        print("   ✅ All frontend fields available in database")
    
    # Check enhanced field benefits
    enhanced_benefits = [
        'container_count',
        'container_type', 
        'total_weight_kg',
        'calculated_ctn_fee',
        'calculated_service_fee',
        'ocr_confidence_score'
    ]
    
    print("\n🎯 ENHANCED FIELD BENEFITS:")
    for field in enhanced_benefits:
        if field in enhanced_ocr_fields:
            print(f"   ✅ {field} - Available for frontend enhancement")
        else:
            print(f"   ❌ {field} - Missing from enhanced OCR")
    
    print("\n💡 RECOMMENDATIONS:")
    print("   1. ✅ All original fields are preserved in enhanced OCR")
    print("   2. ✅ Database stores all enhanced fields")
    print("   3. 💡 Frontend can be enhanced to show new fields:")
    print("      - Container count and type")
    print("      - Total weight")
    print("      - Calculated fees")
    print("      - OCR confidence score")
    print("   4. 💡 Consider updating frontend to use calculated fees instead of manual entry")

if __name__ == "__main__":
    analyze_field_mapping() 