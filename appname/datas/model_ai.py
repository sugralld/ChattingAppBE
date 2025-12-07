import requests
import time

# Configuration for your SIBI API server
SIBI_API_URL = "http://localhost:5001/api/translate"  # Change to your server IP if needed

def get_asl_translation(video_url):
    """Get SIBI translation via API"""
    print(f"🎯 Requesting SIBI translation via API for: {video_url}")
    
    try:
        start_time = time.time()
        
        # Call your SIBI API server
        response = requests.post(
            SIBI_API_URL,
            json={"video_url": video_url},
            timeout=600  # 10 minutes timeout for video processing
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                predictions = result.get("data", [])
                
                print(f"✅ SIBI API request successful")
                print(f"⏱️ Processing time: {processing_time:.2f}s")
                print(f"📊 Signs detected: {len(predictions)}")
                
                # Log each detection
                for pred in predictions[:10]:  # Show first 10
                    print(f"   - {pred.get('second')}s: {pred.get('text')}")
                if len(predictions) > 10:
                    print(f"   ... and {len(predictions) - 10} more")
                
                return predictions
            else:
                error_msg = result.get("message", "Unknown error")
                print(f"❌ SIBI API error: {error_msg}")
                return []
        else:
            print(f"❌ SIBI API HTTP error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"❌ SIBI API timeout after 600 seconds")
        return []
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to SIBI API at {SIBI_API_URL}")
        print(f"   Make sure the SIGNLANGUAGE API server is running")
        return []
    except Exception as e:
        print(f"❌ Error calling SIBI API: {e}")
        return []
    
def fallback_timestamps(total_duration=4.0):
    """Fallback when translation fails"""
    return [
        {"second": 0.0, "text": "SIGN"},
        {"second": 1.0, "text": "LANGUAGE"},
        {"second": 2.0, "text": "DETECTION"},
        {"second": 3.0, "text": "UNAVAILABLE"}
    ]

# Compatibility functions (keep these for your existing code)
def map_prediction_to_asl(predicted_label):
    return predicted_label

def preprocess_frames(frames):
    return frames

def get_top_predictions(logits, top_k=3):
    return [("SIBI_RECOGNITION", 1.0)]

model = None
processor = None

# Add this function to your model_ai.py
def generate_srt_from_predictions(predictions, output_path="output.srt"):
    """Generate SRT subtitle file from predictions"""
    srt_content = ""
    
    for i, pred in enumerate(predictions, 1):
        start_time = pred["second"]
        end_time = start_time + 1.0  # Each sign lasts 1 second
        
        # Convert seconds to SRT time format
        start_timestamp = format_timestamp(start_time)
        end_timestamp = format_timestamp(end_time)
        
        srt_content += f"{i}\n"
        srt_content += f"{start_timestamp} --> {end_timestamp}\n"
        srt_content += f"{pred['text']}\n\n"
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return output_path

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"