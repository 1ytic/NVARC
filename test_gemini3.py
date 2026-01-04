#!/usr/bin/env python3
"""Test script to verify Gemini 3 Flash API connection and basic functionality."""
import os
import json
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()

def test_api_connection():
    """Test basic API connection and response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment")
        print("Please create a .env file with: GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"✓ API key found (length: {len(api_key)} chars)")
    
    try:
        genai.configure(api_key=api_key)
        print("✓ API configured successfully")
    except Exception as e:
        print(f"✗ Failed to configure API: {e}")
        return False
    
    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        print("✓ Model initialized: gemini-3-flash-preview")
    except Exception as e:
        print(f"✗ Failed to initialize model: {e}")
        return False
    
    # Test 1: Simple text generation
    print("\n--- Test 1: Simple text generation ---")
    try:
        prompt = "Say 'hello' in one word."
        response = model.generate_content(prompt)
        
        if not response:
            print("✗ No response object returned")
            return False
        
        # Check for blocking
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                print(f"✗ Response blocked: {response.prompt_feedback.block_reason}")
                return False
        
        # Get text
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                text = ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            else:
                print("✗ Could not extract text from response")
                return False
        else:
            print("✗ Response has no text attribute")
            return False
        
        print(f"✓ Response received: {text[:100]}")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: JSON generation
    print("\n--- Test 2: JSON generation ---")
    try:
        prompt = "Output ONLY this JSON: {\"test\": \"hello\"}"
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            text = ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
        else:
            print("✗ Could not extract text from JSON test")
            return False
        
        print(f"✓ Raw response: {text[:200]}")
        
        # Try to extract JSON
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            data = json.loads(json_text)
            print(f"✓ JSON parsed successfully: {data}")
        else:
            print(f"⚠ No JSON found in response (response: {text[:200]})")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✓ All tests passed! API connection is working.")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Test Gemini 3 Flash API connection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  uv run test_gemini3.py"
    )
    parser.parse_args()
    success = test_api_connection()
    exit(0 if success else 1)
