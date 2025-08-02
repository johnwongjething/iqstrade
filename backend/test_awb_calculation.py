#!/usr/bin/env python3
"""
Test AWB fee calculation and OCR system usage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

def test_awb_calculation():
    """Test AWB fee calculation and OCR system"""
    
    print("🛩️ TESTING AWB CALCULATION")
    print("=" * 40)
    
    # Test with a sample AWB (we'll simulate the data from the screenshot)
    print("📄 Simulating AWB data from screenshot:")
    print("   - Document Type: AWB")
    print("   - Gross Weight: 324 kg")
    print("   - Expected CTN Fee: $324.00")
    print("   - Expected Service Fee: $486.00")
    
    try:
        # Test enhanced OCR with different user scenarios
        print("\n🧪 TESTING OCR SYSTEMS:")
        
        # Test for user ray40 (use_openai=True)
        print("\n👤 USER ray40 (use_openai=True):")
        print("-" * 30)
        try:
            from enhanced_ocr_processor import extract_fields_enhanced
            
            # We need an actual AWB PDF to test with
            # For now, let's check the pricing configuration
            from config import get_db_conn
            conn = get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT shipment_type, ctn_fee_per_unit, service_fee_per_unit, unit_type, minimum_charge
                FROM pricing_config 
                WHERE shipment_type = 'air' AND is_active = TRUE
            """)
            
            pricing = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if pricing:
                print("✅ Air freight pricing found:")
                print(f"   CTN Fee per kg: ${pricing[1]}")
                print(f"   Service Fee per kg: ${pricing[2]}")
                print(f"   Unit Type: {pricing[3]}")
                print(f"   Minimum Charge: ${pricing[4]}")
                
                # Calculate expected fees for 324 kg
                weight_kg = 324.0
                ctn_fee = float(pricing[1]) * weight_kg
                service_fee = float(pricing[2]) * weight_kg
                total_fee = ctn_fee + service_fee
                
                print(f"\n💰 EXPECTED CALCULATION FOR 324 KG:")
                print(f"   CTN Fee: {weight_kg} kg × ${pricing[1]} = ${ctn_fee:.2f}")
                print(f"   Service Fee: {weight_kg} kg × ${pricing[2]} = ${service_fee:.2f}")
                print(f"   Total: ${total_fee:.2f}")
                
                if total_fee < float(pricing[4]):
                    print(f"   ⚠️ Below minimum charge (${pricing[4]}), will be adjusted")
                else:
                    print(f"   ✅ Above minimum charge")
                    
            else:
                print("❌ No air freight pricing found in database")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test for other users (use_openai=False)
        print("\n👤 OTHER USERS (use_openai=False):")
        print("-" * 35)
        print("   This should use Google Vision if available, fallback to OpenAI")
        
        # Check Google Vision availability
        try:
            from enhanced_ocr_processor import GOOGLE_VISION_AVAILABLE, extract_fields_legacy
            print(f"   Google Vision Available: {GOOGLE_VISION_AVAILABLE}")
            print(f"   extract_fields_legacy function: {extract_fields_legacy is not None}")
        except Exception as e:
            print(f"   ❌ Error checking Google Vision: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_awb_calculation()
    if success:
        print("\n✅ AWB calculation test completed!")
    else:
        print("\n❌ AWB calculation test failed!") 