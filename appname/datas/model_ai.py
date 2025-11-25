# model_ai.py - Enhanced version
import requests
import time
from appname.config import *

def get_asl_translation(video_url):
    """Get ASL translation from WLASL API"""
    print(f"🎯 Requesting WLASL translation for: {video_url}")
    
    try:
        # First, test if WLASL API is reachable
        try:
            health_response = requests.get(ASL_API_URL + "/health", timeout=5)
            print(f"🏥 WLASL API Health: {health_response.status_code}")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"📊 Model loaded: {health_data.get('model_loaded')}")
                print(f"📚 Vocabulary: {health_data.get('vocabulary_size')}")
        except Exception as e:
            print(f"⚠️ WLASL API health check failed: {e}")
        
        # Now make the translation request
        start_time = time.time()
        response = requests.post(
            ASL_API_URL + "/translate",
            json={"video_url": video_url},
            timeout=120  # Longer timeout for WLASL translation
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️ WLASL API processing time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📨 WLASL API Response status: {result.get('status')}")
            print(f"📊 Signs detected: {result.get('signs_detected', 0)}")
            print(f"🎯 Unique signs: {result.get('unique_signs', [])}")
            print(f"🤖 Model used: {result.get('model_used', 'Unknown')}")
            
            if result.get("status") == "success":
                data = result.get("data", [])
                print(f"✅ WLASL Translation successful: {len(data)} predictions")
                return data
            else:
                print(f"❌ WLASL API error: {result.get('message')}")
                return []
        else:
            print(f"❌ WLASL API HTTP error: {response.status_code}")
            print(f"❌ Response text: {response.text}")
            return []
            
    except requests.exceptions.Timeout:
        print("⏰ WLASL translation request timeout")
        return []
    except requests.exceptions.ConnectionError:
        print("🔌 Cannot connect to WLASL API - make sure wlasl_api.py is running on localhost:5001")
        return []
    except Exception as e:
        print(f"❌ Error calling WLASL API: {e}")
        return []

def fallback_timestamps(total_duration=4.0):
    """Fallback when WLASL translation fails"""
    return [
        {"second": 0.0, "text": "HELLO"},
        {"second": 1.0, "text": "WLASL"},
        {"second": 2.0, "text": "TRANSLATION"},
        {"second": 3.0, "text": "UNAVAILABLE"}
    ]

# Compatibility functions (keep these for your existing code)
def map_prediction_to_asl(predicted_label):
    return predicted_label

def preprocess_frames(frames):
    return frames

def get_top_predictions(logits, top_k=3):
    return [("ASL_RECOGNITION", 1.0)]

model = None
processor = None