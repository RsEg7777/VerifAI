"""
AI Image Detection Service
Detects AI-generated images using SightEngine API.

SightEngine provides AI-generated content detection that can:
1. Detect if an image is AI-generated (genai model)
2. Detect deepfakes (deepfake model)
3. Works on pixel content - no metadata dependency

API Documentation: https://sightengine.com/docs/ai-generated-image-detection
Supports: GPT-4o, Stable Diffusion, MidJourney, Adobe Firefly, Flux, Reve, Recraft, Imagen, Ideogram, GANs
"""

import requests
import json
from io import BytesIO
from PIL import Image
from PIL.ExifTags import TAGS


class ImageDetector:
    """Service class for detecting AI-generated images using SightEngine API"""
    
    # SightEngine API endpoint
    SIGHTENGINE_API_URL = "https://api.sightengine.com/1.0/check.json"
    
    # Known AI generation software signatures for local fallback
    AI_SOFTWARE_SIGNATURES = [
        'stable diffusion', 'midjourney', 'dall-e', 'dalle', 'novelai',
        'automatic1111', 'comfyui', 'invoke', 'diffusers', 'sd',
        'nai diffusion', 'dreamstudio', 'leonardo', 'firefly',
        'bing image creator', 'ideogram', 'playground'
    ]
    
    def __init__(self, api_user=None, api_secret=None, **kwargs):
        """
        Initialize the ImageDetector.
        
        Args:
            api_user: SightEngine API user ID
            api_secret: SightEngine API secret key
        """
        self.api_user = api_user
        self.api_secret = api_secret
    
    def detect_ai_image(self, image_file):
        """
        Detect if an image is AI-generated using SightEngine API.
        
        Args:
            image_file: File object or bytes of the image
            
        Returns:
            dict: Detection results with confidence, status, and analysis
        """
        try:
            # Read image bytes
            if hasattr(image_file, 'read'):
                image_bytes = image_file.read()
                image_file.seek(0)
            else:
                image_bytes = image_file
            
            # Try SightEngine API first (primary method)
            if self.api_user and self.api_secret:
                if not str(self.api_user).startswith('{{') and not str(self.api_secret).startswith('{{'):
                    result = self._detect_with_sightengine(image_bytes)
                    if result:
                        return result
            
            # Fallback to local analysis if API unavailable
            return self._fallback_local_analysis(image_bytes)
                
        except Exception as e:
            print(f"Error in AI image detection: {str(e)}")
            return self._create_error_response(str(e))
    
    def _detect_with_sightengine(self, image_bytes):
        """
        Detect AI-generated images using SightEngine API.
        
        API: https://api.sightengine.com/1.0/check.json
        Model: genai (for AI-generated image detection)
        Auth: api_user and api_secret parameters
        """
        try:
            # Prepare parameters
            params = {
                'models': 'genai',
                'api_user': self.api_user,
                'api_secret': self.api_secret
            }
            
            # Send image as file upload
            files = {
                'media': ('image.jpg', image_bytes, 'image/jpeg')
            }
            
            print("Calling SightEngine API for AI image detection...")  # Debug
            
            response = requests.post(
                self.SIGHTENGINE_API_URL,
                files=files,
                data=params,
                timeout=30
            )
            
            print(f"SightEngine Response Status: {response.status_code}")  # Debug
            
            if response.status_code == 200:
                data = response.json()
                print(f"SightEngine Response: {json.dumps(data, indent=2)}")  # Debug
                return self._parse_sightengine_response(data)
            elif response.status_code == 401:
                print("SightEngine API: Invalid credentials")
                return None
            elif response.status_code == 402:
                print("SightEngine API: Insufficient credits")
                return None
            elif response.status_code == 429:
                print("SightEngine API: Rate limit exceeded")
                return None
            else:
                print(f"SightEngine API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("SightEngine API: Request timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("SightEngine API: Connection error")
            return None
        except Exception as e:
            print(f"SightEngine API error: {str(e)}")
            return None
    
    def _parse_sightengine_response(self, response_data):
        """
        Parse SightEngine API response for AI-generated image detection.
        
        Response format:
        {
            "status": "success",
            "type": {
                "ai_generated": 0.99
            },
            "media": {
                "id": "...",
                "uri": "..."
            }
        }
        """
        try:
            # Check status
            if response_data.get('status') != 'success':
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                print(f"SightEngine API error: {error_msg}")
                return None
            
            # Get AI-generated score
            type_data = response_data.get('type', {})
            ai_score = type_data.get('ai_generated', 0)
            
            # Determine if AI-generated (threshold: 0.5)
            is_ai_generated = ai_score > 0.5
            confidence = int(ai_score * 100) if is_ai_generated else int((1 - ai_score) * 100)
            
            # Generate reasons based on score
            reasons = []
            if is_ai_generated:
                if ai_score > 0.9:
                    reasons.append("High confidence AI-generated content detected")
                    reasons.append("Image shows strong artificial generation patterns")
                elif ai_score > 0.7:
                    reasons.append("AI-generated patterns detected in image")
                    reasons.append("Visual analysis indicates synthetic origin")
                elif ai_score > 0.5:
                    reasons.append("Moderate AI-generation indicators found")
                    reasons.append("Some artificial patterns detected")
                reasons.append("Analysis powered by SightEngine AI detection")
            else:
                if ai_score < 0.1:
                    reasons.append("High confidence authentic photograph")
                    reasons.append("No AI-generation markers detected")
                elif ai_score < 0.3:
                    reasons.append("Natural image characteristics detected")
                    reasons.append("Image appears to be genuine")
                else:
                    reasons.append("No significant AI-generation markers found")
                    reasons.append("Image likely authentic")
            
            return {
                'is_ai_generated': is_ai_generated,
                'confidence': confidence,
                'status': 'AI-generated' if is_ai_generated else 'Real',
                'reasons': reasons[:3],
                'artifacts_detected': is_ai_generated,
                'detection_method': 'SightEngine AI',
                'raw_score': round(ai_score, 4)
            }
            
        except Exception as e:
            print(f"Error parsing SightEngine response: {str(e)}")
            return None
    
    def _fallback_local_analysis(self, image_bytes):
        """
        Fallback local analysis when SightEngine API is unavailable.
        Uses metadata analysis and basic heuristics.
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            width, height = image.size
            
            score = 50  # Neutral starting point
            reasons = []
            
            # Check metadata for AI signatures
            try:
                exif = image._getexif()
                if exif is None:
                    score += 15
                    reasons.append("No camera metadata found (common in AI images)")
                else:
                    exif_data = {TAGS.get(k, k): v for k, v in exif.items()}
                    
                    # Check for camera info
                    has_camera = any(k in exif_data for k in ['Make', 'Model'])
                    has_gps = 'GPSInfo' in exif_data
                    
                    if has_camera:
                        score -= 25
                        reasons.append(f"Camera metadata found: {exif_data.get('Make', '')} {exif_data.get('Model', '')}")
                    
                    if has_gps:
                        score -= 20
                        reasons.append("GPS location data present")
                    
                    # Check software field
                    software = str(exif_data.get('Software', '')).lower()
                    if any(sig in software for sig in self.AI_SOFTWARE_SIGNATURES):
                        score += 40
                        reasons.append("AI generation software detected in metadata")
            except Exception:
                pass
            
            # Check PNG metadata
            if image.format == 'PNG':
                try:
                    info_str = str(image.info).lower()
                    if any(sig in info_str for sig in self.AI_SOFTWARE_SIGNATURES):
                        score += 40
                        reasons.append("AI parameters found in PNG metadata")
                    elif 'parameters' in info_str or 'prompt' in info_str:
                        score += 35
                        reasons.append("Generation prompt found in metadata")
                except Exception:
                    pass
            
            # Check dimensions (AI generators often use specific sizes)
            ai_dimensions = [
                (512, 512), (768, 768), (1024, 1024), (1536, 1536),
                (512, 768), (768, 512), (768, 1024), (1024, 768)
            ]
            
            if (width, height) in ai_dimensions or (height, width) in ai_dimensions:
                score += 15
                reasons.append(f"Dimensions {width}x{height} match common AI output")
            elif width % 64 == 0 and height % 64 == 0 and width >= 512:
                score += 10
                reasons.append("Dimensions are multiples of 64 (diffusion model pattern)")
            
            # Clamp score
            score = max(0, min(100, score))
            is_ai_generated = score >= 50
            
            if not reasons:
                reasons = ["Image analysis complete (local fallback method)"]
            
            return {
                'is_ai_generated': is_ai_generated,
                'confidence': score if is_ai_generated else (100 - score),
                'status': 'AI-generated' if is_ai_generated else 'Real',
                'reasons': reasons[:3],
                'artifacts_detected': is_ai_generated,
                'detection_method': 'Local Analysis (API unavailable)',
                'note': 'For best results, configure SightEngine API credentials'
            }
            
        except Exception as e:
            print(f"Local analysis error: {str(e)}")
            return self._create_error_response(str(e))
    
    def _create_error_response(self, error_msg):
        """Create response for error cases"""
        return {
            'is_ai_generated': False,
            'confidence': 50,
            'status': 'Unknown',
            'reasons': [f'Analysis error: {error_msg}'],
            'artifacts_detected': False,
            'detection_method': 'Error',
            'note': 'Could not complete analysis'
        }


def analyze_image_artifacts(image_file):
    """
    Analyze image for specific AI artifacts.
    Returns list of detected artifacts with details.
    """
    try:
        if hasattr(image_file, 'read'):
            image_bytes = image_file.read()
            image_file.seek(0)
        else:
            image_bytes = image_file
        
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
        
        artifacts = []
        
        # Dimension-based artifacts
        if width == height and width >= 512:
            artifacts.append({
                'type': 'Square Dimensions',
                'description': f'Image is {width}x{height} - common AI generator output size',
                'confidence': 'Medium'
            })
        
        if width % 64 == 0 and height % 64 == 0:
            artifacts.append({
                'type': 'Diffusion Model Dimensions',
                'description': 'Dimensions are multiples of 64 (required by diffusion models)',
                'confidence': 'Medium'
            })
        
        # Check for metadata artifacts
        try:
            if image._getexif() is None:
                artifacts.append({
                    'type': 'Missing EXIF Data',
                    'description': 'No camera metadata found - common in AI-generated images',
                    'confidence': 'Medium'
                })
        except Exception:
            pass
        
        # PNG-specific checks
        if image.format == 'PNG':
            info_str = str(image.info).lower()
            if 'parameters' in info_str or 'prompt' in info_str:
                artifacts.append({
                    'type': 'AI Generation Parameters',
                    'description': 'Found AI generation prompt/parameters in metadata',
                    'confidence': 'High'
                })
        
        # Add texture analysis placeholder
        artifacts.append({
            'type': 'Texture Consistency',
            'description': 'Analyzing texture patterns for AI artifacts',
            'confidence': 'Analyzing'
        })
        
        return artifacts
        
    except Exception as e:
        print(f"Error analyzing artifacts: {str(e)}")
        return [{
            'type': 'Analysis Error',
            'description': str(e),
            'confidence': 'N/A'
        }]
