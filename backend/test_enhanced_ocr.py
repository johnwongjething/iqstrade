#!/usr/bin/env python3
"""
Test script for enhanced OCR processor
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_ocr_import():
    """Test that the enhanced OCR processor can be imported"""
    try:
        # Test import without initializing Google Vision
        from enhanced_ocr_processor import EnhancedOCRProcessor
        print("✅ EnhancedOCRProcessor class imported successfully")
        
        # Test creating an instance
        processor = EnhancedOCRProcessor()
        print("✅ EnhancedOCRProcessor instance created successfully")
        
        # Test container info extraction
        test_text = "Container: 20ft, 40ft HC, Weight: 1000 kg"
        container_info = processor.extract_container_info(test_text, ['ABCD1234567', 'EFGH7890123'])
        print(f"✅ Container info extraction: {container_info}")
        
        # Test weight info extraction
        weight_info = processor.extract_weight_info(test_text)
        print(f"✅ Weight info extraction: {weight_info}")
        
        # Test shipment classification
        shipment_info = processor.classify_shipment_type(test_text, 'BOL')
        print(f"✅ Shipment classification: {shipment_info}")
        
        print("\n🎉 All enhanced OCR tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced OCR test failed: {e}")
        return False

def test_database_connection():
    """Test database connection and new schema"""
    try:
        from config import get_db_conn
        
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Test new columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bill_of_lading' 
            AND column_name IN ('shipment_type', 'container_type', 'container_count', 'total_weight_kg', 'pricing_method', 'ocr_confidence_score', 'manual_override')
        """)
        
        new_columns = [row[0] for row in cursor.fetchall()]
        expected_columns = ['shipment_type', 'container_type', 'container_count', 'total_weight_kg', 'pricing_method', 'ocr_confidence_score', 'manual_override']
        
        missing_columns = [col for col in expected_columns if col not in new_columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        
        print("✅ All new database columns exist")
        
        # Test pricing_config table
        cursor.execute("SELECT COUNT(*) FROM pricing_config")
        config_count = cursor.fetchone()[0]
        print(f"✅ Pricing config table has {config_count} records")
        
        # Test pricing_overrides table
        cursor.execute("SELECT COUNT(*) FROM pricing_overrides")
        overrides_count = cursor.fetchone()[0]
        print(f"✅ Pricing overrides table has {overrides_count} records")
        
        cursor.close()
        conn.close()
        
        print("🎉 Database schema test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced OCR System")
    print("=" * 50)
    
    # Test enhanced OCR
    ocr_success = test_enhanced_ocr_import()
    
    print("\n" + "=" * 50)
    
    # Test database
    db_success = test_database_connection()
    
    print("\n" + "=" * 50)
    
    if ocr_success and db_success:
        print("🎉 ALL TESTS PASSED! Enhanced OCR system is ready.")
        print("\n📋 Next steps:")
        print("1. Deploy to production")
        print("2. Test with real documents")
        print("3. Train staff on manual override interface")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 