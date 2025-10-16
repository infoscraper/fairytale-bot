#!/usr/bin/env python3
"""
Debug Google credentials JSON
"""
import os
import json

def debug_credentials():
    """Debug Google credentials"""
    
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if not creds_json:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
        return
    
    print(f"📋 Credentials length: {len(creds_json)} characters")
    print(f"📋 First 100 chars: {creds_json[:100]}")
    print(f"📋 Last 100 chars: {creds_json[-100:]}")
    
    try:
        # Try to parse JSON
        creds_data = json.loads(creds_json)
        print("✅ JSON is valid!")
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field in creds_data:
                print(f"✅ {field}: present")
            else:
                print(f"❌ {field}: missing")
        
        # Test writing to file
        temp_path = "/tmp/test_gsa.json"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(creds_data, f, indent=2)
        
        print(f"✅ Successfully wrote to {temp_path}")
        
        # Try to read back
        with open(temp_path, "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        print("✅ Successfully read back from file")
        
        # Clean up
        os.remove(temp_path)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Error at position {e.pos}")
        if e.pos < len(creds_json):
            start = max(0, e.pos - 50)
            end = min(len(creds_json), e.pos + 50)
            print(f"Context: ...{creds_json[start:end]}...")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    debug_credentials()
