from flask import Flask, request, jsonify, render_template, redirect, url_for
import ollama
import requests
import json
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse
from datetime import datetime
from flask_mail import Mail, Message
from flask_login import LoginManager, current_user, login_required
from config import Config
from models import db, User, UserHistory, SavedArticle, VerificationResult, SearchQuery, ImageDetectionResult
from auth import auth as auth_blueprint
from image_detector import ImageDetector, analyze_image_artifacts
from source_data import get_source_info, get_bias_label, get_credibility_label, BIAS_COLORS, CREDIBILITY_COLORS
import os
from werkzeug.utils import secure_filename

# Multilingual support imports
try:
    from langdetect import detect as detect_language_code
    from deep_translator import GoogleTranslator
    MULTILINGUAL_ENABLED = True
except ImportError:
    MULTILINGUAL_ENABLED = False
    print("Warning: langdetect or deep-translator not installed. Multilingual support disabled.")

# OCR support imports for meme/quote detection
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_ENABLED = True
    
    # Configure Tesseract path for Windows
    import platform
    if platform.system() == 'Windows':
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
except ImportError:
    OCR_ENABLED = False
    print("Warning: pytesseract or opencv not installed. OCR meme detection disabled.")

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'mr': 'Marathi'
}

# Initialize translator (deep-translator doesn't need initialization)

# Create the Flask app
app = Flask(__name__)

# Load configuration from Config class
app.config.from_object(Config)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize SQLAlchemy
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Google Custom Search setup
API_KEY = Config.GOOGLE_API_KEY
CSE_ID = Config.GOOGLE_CSE_ID

def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CSE_ID,
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Error with Google Search API: {response.status_code}")
    
    # Extract only the URLs from the search results
    search_results = response.json()
    urls = []
    if 'items' in search_results:
        urls = [item['link'] for item in search_results['items']]
    
    return urls

# ============================================
# MULTILINGUAL SUPPORT FUNCTIONS (Feature 5)
# ============================================

def detect_language(text):
    """
    Detect the language of the given text
    Returns language code (en, hi, mr) or 'en' as default
    """
    if not MULTILINGUAL_ENABLED:
        return 'en'
    
    try:
        lang_code = detect_language_code(text)
        # Map detected language to supported languages
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
        return 'en'  # Default to English if not supported
    except Exception as e:
        print(f"Language detection error: {str(e)}")
        return 'en'

def translate_to_english(text, source_lang=None):
    """
    Translate text to English for verification
    Returns tuple: (translated_text, detected_language)
    """
    if not MULTILINGUAL_ENABLED:
        return text, 'en'
    
    try:
        # Detect language if not provided
        if not source_lang:
            source_lang = detect_language(text)
        
        # If already English, return as-is
        if source_lang == 'en':
            return text, 'en'
        
        # Translate to English using deep-translator
        translated = GoogleTranslator(source=source_lang, target='en').translate(text)
        return translated, source_lang
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text, 'en'

def translate_from_english(text, target_lang):
    """
    Translate English text back to target language
    """
    if not MULTILINGUAL_ENABLED:
        return text
    
    try:
        # If target is English, return as-is
        if target_lang == 'en':
            return text
        
        # Translate to target language using deep-translator
        translated = GoogleTranslator(source='en', target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text

def translate_analysis_result(result, target_lang):
    """
    Translate all text fields in analysis result to target language
    """
    if not MULTILINGUAL_ENABLED or target_lang == 'en':
        return result
    
    try:
        translated = result.copy()
        
        # Translate key findings
        if 'key_findings' in translated:
            translated['key_findings'] = [
                translate_from_english(f, target_lang) for f in translated['key_findings']
            ]
        
        # Translate differences
        if 'differences' in translated:
            translated['differences'] = [
                translate_from_english(d, target_lang) for d in translated['differences']
            ]
        
        # Translate claims analysis
        if 'claims_analysis' in translated:
            for claim in translated['claims_analysis']:
                if claim.get('explanation'):
                    claim['explanation'] = translate_from_english(claim['explanation'], target_lang)
                if claim.get('corrected_statement'):
                    claim['corrected_statement'] = translate_from_english(claim['corrected_statement'], target_lang)
        
        # Translate bias indicators
        if 'bias_detection' in translated and translated['bias_detection'].get('indicators'):
            translated['bias_detection']['indicators'] = [
                translate_from_english(i, target_lang) for i in translated['bias_detection']['indicators']
            ]
        
        # Translate emotional manipulation examples
        if 'emotional_manipulation' in translated and translated['emotional_manipulation'].get('examples'):
            translated['emotional_manipulation']['examples'] = [
                translate_from_english(e, target_lang) for e in translated['emotional_manipulation']['examples']
            ]
        
        # Translate sensational indicators
        if 'sensational_tone' in translated and translated['sensational_tone'].get('indicators'):
            translated['sensational_tone']['indicators'] = [
                translate_from_english(i, target_lang) for i in translated['sensational_tone']['indicators']
            ]
        
        return translated
    except Exception as e:
        print(f"Translation of results error: {str(e)}")
        return result

@app.route('/detect_language', methods=['POST'])
def api_detect_language():
    """API endpoint to detect language of text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        lang_code = detect_language(text)
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')
        
        return jsonify({
            'language_code': lang_code,
            'language_name': lang_name,
            'supported': lang_code in SUPPORTED_LANGUAGES,
            'multilingual_enabled': MULTILINGUAL_ENABLED
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/translate', methods=['POST'])
def api_translate():
    """API endpoint to translate text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        target_lang = data.get('target_lang', 'en')
        source_lang = data.get('source_lang')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        if not MULTILINGUAL_ENABLED:
            return jsonify({
                'translated_text': text,
                'source_lang': 'en',
                'target_lang': target_lang,
                'message': 'Translation not available'
            })
        
        if target_lang == 'en':
            translated, detected = translate_to_english(text, source_lang)
        else:
            if source_lang and source_lang != 'en':
                # First translate to English, then to target
                english_text, _ = translate_to_english(text, source_lang)
                translated = translate_from_english(english_text, target_lang)
            else:
                translated = translate_from_english(text, target_lang)
            detected = source_lang or 'en'
        
        return jsonify({
            'translated_text': translated,
            'source_lang': detected,
            'target_lang': target_lang
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_key_phrases_with_ollama(text):
    prompt = f"""
        You are a professional news analyst.
        Please extract 3 concise headlines from the following news article. 
        Make sure that each headlines are clear and concise, focusing on the main facts and events,places,people,organizations,date-time,etc.
    I have this news article:\n\n{text}\n\n
    Please provide a response in pure JSON format():
    {{
        "news_headline": [
            "news_headline_1",
            "news_headline_2",
            "news_headline_3"
        ]
    }}
    """
    
    response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
    
    if 'message' in response and 'content' in response['message']:
        try:
            # Extract JSON from the response content
            content = response['message']['content']
            # Find the JSON object in the response
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            raise
    return None

@app.route('/')
def index():
    return render_template('index.html', active_page='home')

@app.route('/diagrams')
def diagrams():
    return render_template('diagrams.html', active_page='diagrams')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json()
        news_text = data.get('news')
        
        if not news_text:
            return jsonify({'error': 'No news text provided'}), 400

        # Extract key phrases using Ollama
        result = extract_key_phrases_with_ollama(news_text)
        
        if not result or 'news_headline' not in result:
            return jsonify({'error': 'Failed to extract headlines'}), 500

        return jsonify({'key_phrases': result})

    except Exception as e:
        print(f"Error in extract endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        news_text = data.get('news')
        
        if not news_text:
            return jsonify({'error': 'No news text provided'}), 400

        # Perform Google search
        search_results = google_search(news_text)
        
        return jsonify({
            'google_search_results': search_results
        })

    except Exception as e:
        print(f"Error in search endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add this function to extract content and metadata from URLs
def extract_article_content(url):
    try:
        # Download content
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            return None

        # Extract main content
        content = trafilatura.extract(downloaded)
        
        # Get metadata using BeautifulSoup as backup
        soup = BeautifulSoup(downloaded, 'html.parser')
        title = soup.title.string if soup.title else ''
        
        # Parse the URL to get the source
        source = urlparse(url).netloc.replace('www.', '')
        
        # Find image (first image in article or og:image)
        image_url = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content')
        
        # Get source transparency info
        source_info = get_source_info(source)
        
        return {
            'url': url,
            'title': title,
            'content': content,  
            'description': content[:300] + '...' if content else '',
            'source': source,
            'image_url': image_url,
            'source_info': {
                'name': source_info.get('name', source),
                'bias': source_info.get('bias', 'unknown'),
                'bias_label': get_bias_label(source_info.get('bias', 'unknown')),
                'credibility': source_info.get('credibility', 'unknown'),
                'credibility_label': get_credibility_label(source_info.get('credibility', 'unknown')),
                'description': source_info.get('description', ''),
                'bias_color': BIAS_COLORS.get(source_info.get('bias', 'unknown'), '#6b7280'),
                'credibility_color': CREDIBILITY_COLORS.get(source_info.get('credibility', 'unknown'), '#6b7280')
            }
        }
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None

# Add new route for displaying extracted content
@app.route('/extracted_content', methods=['POST'])
def show_extracted_content():
    try:
        data = request.get_json()
        original_news = data.get('news')
        urls = data.get('urls', [])

        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400

        # Extract content from each URL
        extracted_articles = []
        for url in urls[:3]:  # Limit to top 3 URLs
            article_content = extract_article_content(url)
            if article_content:
                extracted_articles.append(article_content)

        return render_template('extracted_content.html',
                             original_news=original_news,
                             extracted_articles=extracted_articles,
                             active_page='home')

    except Exception as e:
        print(f"Error in extracted_content endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results', methods=['POST'])
def show_results():
    try:
        data = request.get_json()
        original_news = data.get('news')
        headlines = data.get('headlines', [])
        
        if not headlines:
            return jsonify({'error': 'No headlines provided'}), 400

        search_results = []
        
        # Create search query record in database
        search_query = SearchQuery(query_text=original_news)
        search_query.set_headlines(headlines)
        
        # Associate with user if logged in
        if current_user.is_authenticated:
            search_query.user_id = current_user.id
        
        db.session.add(search_query)
        db.session.commit()
        
        # Process each headline
        for headline in headlines:
            # Search for URLs
            urls = google_search(headline)
            
            # Extract content from URLs
            articles = []
            for url in urls[:3]:  # Limit to top 3 URLs per headline
                article_content = extract_article_content(url)
                if article_content:
                    articles.append(article_content)
            
            # Add to results if we found articles
            if articles:
                search_results.append({
                    'headline': headline,
                    'articles': articles
                })
        
        # Update search query with results
        search_query.set_search_results({headline: [a['url'] for a in result['articles']] 
                                        for result in search_results 
                                        for headline in [result['headline']]})
        db.session.commit()
        
        # Add to user history if logged in
        if current_user.is_authenticated:
            history_entry = UserHistory(
                user_id=current_user.id,
                action_type='search_performed',
                action_details=f'Search with {len(headlines)} headlines',
                article_title=f'Search #{search_query.id}'
            )
            db.session.add(history_entry)
            db.session.commit()

        # Get current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('search_results.html',
                             original_news=original_news,
                             search_results=search_results,
                             current_time=current_time,
                             active_page='home')

    except Exception as e:
        print(f"Error in results endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add this new function after your existing functions
def analyze_authenticity(original_news, verified_articles):
    # Prepare the content for comparison
    verified_contents = [article['content'] for article in verified_articles if article['content']]
    
    if not verified_contents:
        return {
            "authenticity_score": 0,
            "key_findings": ["No verified sources available for comparison"],
            "differences": ["Unable to verify due to lack of reference content"],
            "supporting_evidence": [{"quote": "No verified sources found", "source": "System"}],
            "score_breakdown": {
                "factual_accuracy": 0,
                "source_consistency": 0,
                "detail_accuracy": 0,
                "context_accuracy": 0
            }
        }

    # Enhanced prompt with detailed claim-by-claim analysis
    prompt = f"""
    You are a professional fact-checker and news analyst.
    Analyze the given content for misinformation by comparing against trusted sources.
    
    Original News Article:
    {original_news}

    Trusted Sources:
    {' '.join(verified_contents[:3])}

    Perform a detailed analysis:
    1. Identify each claim in the article and classify it as:
       - "verified_true" - Confirmed by trusted sources
       - "misleading" - Partially true but missing context
       - "false" - Contradicted by trusted sources
       - "unverified" - Cannot be confirmed
    
    2. For every misleading or false claim, provide:
       - The exact sentence from the article
       - Why it is misleading/false
       - Missing context if any
       - Corrected factual statement
       - Confidence percentage (0-100)
    
    3. Detect and report:
       - Bias indicators (political lean, one-sided reporting)
       - Emotional manipulation tactics (fear, anger, outrage triggers)
       - Sensational headline/tone (clickbait, exaggeration)
       - Hallucinated or unsourced statistics
    
    Respond with a JSON object containing:
    {{
        "authenticity_score": <0-100>,
        "key_findings": ["finding1", "finding2", "finding3"],
        "differences": ["difference1", "difference2"],
        "supporting_evidence": [{{"quote": "...", "source": "..."}}],
        "score_breakdown": {{
            "factual_accuracy": <0-40>,
            "source_consistency": <0-30>,
            "detail_accuracy": <0-20>,
            "context_accuracy": <0-10>
        }},
        "claims_analysis": [
            {{
                "claim": "exact sentence from article",
                "classification": "verified_true|misleading|false|unverified",
                "explanation": "why this classification",
                "corrected_statement": "factual correction if needed",
                "confidence": <0-100>
            }}
        ],
        "bias_detection": {{
            "detected": true/false,
            "type": "political|commercial|sensational|none",
            "indicators": ["indicator1", "indicator2"]
        }},
        "emotional_manipulation": {{
            "detected": true/false,
            "tactics": ["fear", "anger", "urgency", etc.],
            "examples": ["example phrase from text"]
        }},
        "sensational_tone": {{
            "detected": true/false,
            "score": <0-100>,
            "indicators": ["clickbait phrases", "exaggerations"]
        }}
    }}
    """

    try:
        # Call the LLM with enhanced analysis prompt
        response = ollama.chat(model='llama3.2', messages=[
            {
                "role": "system",
                "content": "You are a professional fact-checker, news analyst, and misinformation expert. Analyze content thoroughly and respond only with clean JSON. Include claim-by-claim analysis, bias detection, emotional manipulation detection, and sensational tone analysis."
            },
            {
                "role": "user",
                "content": prompt
            }
        ])

        # Extract content from response
        if not response or 'message' not in response or 'content' not in response['message']:
            return create_error_response("Invalid response from LLM")

        content = response['message']['content'].strip()
        
        # Extract JSON from the response
        try:
            # Find JSON object in the response
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                result = json.loads(json_str)
                
                # Create a standardized response with defaults for missing fields
                analysis = {
                    "authenticity_score": 0,
                    "key_findings": [],
                    "differences": [],
                    "supporting_evidence": [],
                    "score_breakdown": {
                        "factual_accuracy": 0,
                        "source_consistency": 0,
                        "detail_accuracy": 0,
                        "context_accuracy": 0
                    },
                    "claims_analysis": [],
                    "bias_detection": {
                        "detected": False,
                        "type": "none",
                        "indicators": []
                    },
                    "emotional_manipulation": {
                        "detected": False,
                        "tactics": [],
                        "examples": []
                    },
                    "sensational_tone": {
                        "detected": False,
                        "score": 0,
                        "indicators": []
                    }
                }
                
                # Extract and validate authenticity score
                try:
                    score = int(result.get('authenticity_score', 0))
                    analysis["authenticity_score"] = max(0, min(100, score))
                except (ValueError, TypeError):
                    pass
                
                # Extract key findings (up to 3)
                findings = result.get('key_findings', [])
                if isinstance(findings, list):
                    analysis["key_findings"] = [str(f) for f in findings[:3]]
                
                # Extract differences (up to 3)
                differences = result.get('differences', [])
                if isinstance(differences, list):
                    analysis["differences"] = [str(d) for d in differences[:3]]
                
                # Extract supporting evidence (up to 3)
                evidence = result.get('supporting_evidence', [])
                if isinstance(evidence, list):
                    for item in evidence[:3]:
                        if isinstance(item, dict):
                            analysis["supporting_evidence"].append({
                                "quote": str(item.get('quote', '')),
                                "source": str(item.get('source', 'Unknown'))
                            })
                
                # Extract score breakdown
                breakdown = result.get('score_breakdown', {})
                if isinstance(breakdown, dict):
                    try:
                        analysis["score_breakdown"] = {
                            "factual_accuracy": max(0, min(40, int(breakdown.get('factual_accuracy', 0)))),
                            "source_consistency": max(0, min(30, int(breakdown.get('source_consistency', 0)))),
                            "detail_accuracy": max(0, min(20, int(breakdown.get('detail_accuracy', 0)))),
                            "context_accuracy": max(0, min(10, int(breakdown.get('context_accuracy', 0))))
                        }
                    except (ValueError, TypeError):
                        pass
                
                # Extract claims analysis
                claims = result.get('claims_analysis', [])
                if isinstance(claims, list):
                    for claim in claims[:10]:  # Limit to 10 claims
                        if isinstance(claim, dict):
                            analysis["claims_analysis"].append({
                                "claim": str(claim.get('claim', '')),
                                "classification": str(claim.get('classification', 'unverified')),
                                "explanation": str(claim.get('explanation', '')),
                                "corrected_statement": str(claim.get('corrected_statement', '')),
                                "confidence": max(0, min(100, int(claim.get('confidence', 50))))
                            })
                
                # Extract bias detection
                bias = result.get('bias_detection', {})
                if isinstance(bias, dict):
                    analysis["bias_detection"] = {
                        "detected": bool(bias.get('detected', False)),
                        "type": str(bias.get('type', 'none')),
                        "indicators": [str(i) for i in bias.get('indicators', [])[:5]]
                    }
                
                # Extract emotional manipulation
                emotional = result.get('emotional_manipulation', {})
                if isinstance(emotional, dict):
                    analysis["emotional_manipulation"] = {
                        "detected": bool(emotional.get('detected', False)),
                        "tactics": [str(t) for t in emotional.get('tactics', [])[:5]],
                        "examples": [str(e) for e in emotional.get('examples', [])[:5]]
                    }
                
                # Extract sensational tone
                sensational = result.get('sensational_tone', {})
                if isinstance(sensational, dict):
                    analysis["sensational_tone"] = {
                        "detected": bool(sensational.get('detected', False)),
                        "score": max(0, min(100, int(sensational.get('score', 0)))),
                        "indicators": [str(i) for i in sensational.get('indicators', [])[:5]]
                    }
                
                return analysis
            else:
                return create_error_response("Could not find JSON in LLM response")
                
        except json.JSONDecodeError:
            return create_error_response("Failed to parse LLM response")

    except Exception as e:
        print(f"Error in analyze_authenticity: {str(e)}")
        return create_error_response(f"Analysis failed: {str(e)}")

def create_error_response(error_message):
    return {
        "authenticity_score": 0,
        "key_findings": [error_message],
        "differences": ["Analysis failed"],
        "supporting_evidence": [{"quote": "Error processing request", "source": "System"}],
        "score_breakdown": {
            "factual_accuracy": 0,
            "source_consistency": 0,
            "detail_accuracy": 0,
            "context_accuracy": 0
        },
        "claims_analysis": [],
        "bias_detection": {"detected": False, "type": "none", "indicators": []},
        "emotional_manipulation": {"detected": False, "tactics": [], "examples": []},
        "sensational_tone": {"detected": False, "score": 0, "indicators": []}
    }

@app.route('/analyze_authenticity', methods=['POST'])
def get_authenticity_analysis():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data received")

        original_news = data.get('original_news')
        verified_articles = data.get('verified_articles', [])
        
        if not original_news:
            raise ValueError("No original news content provided")
            
        analysis_result = analyze_authenticity(original_news, verified_articles)
        
        # Store verification result in database if user is logged in
        if current_user.is_authenticated:
            # Create verification result record
            verification = VerificationResult(
                user_id=current_user.id,
                original_text=original_news,
                authenticity_score=analysis_result['authenticity_score']
            )
            
            # Set JSON fields
            verification.set_key_findings(analysis_result['key_findings'])
            verification.set_differences(analysis_result['differences'])
            verification.set_supporting_evidence(analysis_result['supporting_evidence'])
            verification.set_score_breakdown(analysis_result['score_breakdown'])
            
            # Add to database
            db.session.add(verification)
            
            # Add to user history
            history_entry = UserHistory(
                user_id=current_user.id,
                action_type='article_verified',
                action_details=f'Article verified with score: {analysis_result["authenticity_score"]}%',
                article_title='Verification #' + str(verification.id)
            )
            db.session.add(history_entry)
            db.session.commit()
        
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"Error in get_authenticity_analysis: {str(e)}")
        return jsonify({
            "authenticity_score": 0,
            "key_findings": ["Error during analysis"],
            "differences": ["Analysis failed"],
            "supporting_evidence": [{"quote": "Unable to process", "source": "System"}],
            "score_breakdown": {
                "factual_accuracy": 0,
                "source_consistency": 0,
                "detail_accuracy": 0,
                "context_accuracy": 0
            }
        }), 200  # Return 200 instead of 500 to handle error gracefully

@app.route('/about')
def about():
    try:
        return render_template('about.html', active_page='about')
    except Exception as e:
        print(f"Error rendering about page: {str(e)}")
        return redirect('/')

@app.route('/how-it-works')
def how_it_works():
    try:
        return render_template('how-it-works.html', active_page='how-it-works')
    except Exception as e:
        print(f"Error rendering how-it-works page: {str(e)}")
        return redirect('/')

@app.route('/contact')
def contact():
    try:
        return render_template('contact.html', active_page='contact')
    except Exception as e:
        print(f"Error rendering contact page: {str(e)}")
        return redirect('/')

@app.route('/faq')
def faq():
    try:
        return render_template('faq.html', active_page='faq')
    except Exception as e:
        print(f"Error rendering FAQ page: {str(e)}")
        return redirect('/')

@app.route('/documentation')
def documentation():
    try:
        return render_template('documentation.html', active_page='documentation')
    except Exception as e:
        print(f"Error rendering documentation page: {str(e)}")
        return redirect('/')

@app.route('/save_article', methods=['POST'])
@login_required
def save_article():
    try:
        data = request.get_json()
        article_url = data.get('article_url')
        article_title = data.get('article_title')
        article_content = data.get('article_content')
        article_source = data.get('article_source')
        image_url = data.get('image_url')
        
        if not article_url or not article_title:
            return jsonify({'error': 'URL and title are required'}), 400
            
        # Check if article is already saved
        existing = SavedArticle.query.filter_by(user_id=current_user.id, article_url=article_url).first()
        if existing:
            return jsonify({'message': 'Article already saved', 'saved': True}), 200
        
        # Create new saved article
        saved_article = SavedArticle(
            user_id=current_user.id,
            article_url=article_url,
            article_title=article_title,
            article_content=article_content,
            article_source=article_source,
            image_url=image_url
        )
        
        # Add to database
        db.session.add(saved_article)
        
        # Add to user history
        history_entry = UserHistory(
            user_id=current_user.id,
            action_type='article_saved',
            action_details=f'Saved article: {article_title[:50]}...',
            article_url=article_url,
            article_title=article_title
        )
        db.session.add(history_entry)
        db.session.commit()
        
        return jsonify({'message': 'Article saved successfully', 'saved': True}), 200
        
    except Exception as e:
        print(f"Error saving article: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api-access')
def api_access():
    try:
        return render_template('api-access.html', active_page='api-access')
    except Exception as e:
        print(f"Error rendering API access page: {str(e)}")
        return redirect('/')

@app.route('/case-studies')
def case_studies():
    try:
        return render_template('case-studies.html', active_page='case-studies')
    except Exception as e:
        print(f"Error rendering case studies page: {str(e)}")
        return redirect('/')

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    print(request.json)  # Debugging: Check if JSON data is received


    try:
        # Extract data from the JSON payload
        name = request.json.get('name')
        email = request.json.get('email')
        subject = request.json.get('subject')
        message = request.json.get('message')

        if not name or not email or not message:
            return jsonify({'error': 'Please fill out all fields'}), 400

        # Create the email message
        body = f"Name: {name}\nEmail: {email}\n\nSubject:{subject}\n\nMessage: {message}"

        msg = Message(subject=subject,
                      sender='surajdhasadeyt2913@gmail.com',
                      recipients=['helloworlld4044@gmail.com'])
        msg.body = body
        mail.send(msg)

        return jsonify({'message': 'Form submitted successfully! We will get back to you shortly.'}), 200

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({'error': 'Failed to submit form'}), 500

# ============================================
# TEXT VERIFICATION ROUTES (Feature 2A)
# ============================================

@app.route('/text-verification')
def text_verification():
    """Page for verifying WhatsApp forwards, tweets, social media text"""
    try:
        return render_template('text_verification.html', active_page='text-verification')
    except Exception as e:
        print(f"Error rendering text verification page: {str(e)}")
        return redirect('/')

def verify_text_with_llama(text, original_lang='en'):
    """
    Verify credibility of social media text/WhatsApp forwards using Llama 3.2
    """
    prompt = f"""
    You are an expert fact-checker specialized in identifying misinformation in social media posts and WhatsApp forwards.
    
    Analyze the following text for credibility:
    
    TEXT TO VERIFY:
    {text}
    
    Perform a detailed analysis:
    1. Identify the main claims in the text
    2. Assess each claim's credibility
    3. Look for red flags like:
       - Lack of credible sources
       - Emotional manipulation
       - Urgency tactics ("share before deleted!")
       - Unverified statistics
       - Anonymous sources
       - Conspiracy language
    4. Check for common misinformation patterns
    
    Respond with a JSON object:
    {{
        "credibility_score": <0-100>,
        "verdict": "Likely True" | "Needs Verification" | "Likely False" | "Misinformation",
        "claims": [
            {{
                "claim": "the claim text",
                "assessment": "true|unverified|false|misleading",
                "explanation": "why this assessment"
            }}
        ],
        "red_flags": ["list of red flags found"],
        "recommendations": ["what user should do to verify"],
        "summary": "brief summary of analysis"
    }}
    """
    
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {
                "role": "system",
                "content": "You are a fact-checker expert. Analyze social media content and WhatsApp forwards for misinformation. Respond only with clean JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        if 'message' in response and 'content' in response['message']:
            content = response['message']['content'].strip()
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                result = json.loads(json_str)
                
                # Ensure all expected fields exist
                return {
                    "credibility_score": result.get("credibility_score", 50),
                    "verdict": result.get("verdict", "Needs Verification"),
                    "claims": result.get("claims", []),
                    "red_flags": result.get("red_flags", []),
                    "recommendations": result.get("recommendations", []),
                    "summary": result.get("summary", "Analysis completed"),
                    "original_language": original_lang
                }
    except Exception as e:
        print(f"Error in text verification: {str(e)}")
    
    return {
        "credibility_score": 50,
        "verdict": "Needs Verification",
        "claims": [],
        "red_flags": ["Unable to perform complete analysis"],
        "recommendations": ["Try verifying from official sources"],
        "summary": "Analysis could not be completed fully",
        "original_language": original_lang
    }

@app.route('/verify_text', methods=['POST'])
def verify_text():
    """
    API endpoint to verify WhatsApp forwards, tweets, and social media text
    Supports multilingual input (Hindi, Marathi, English)
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Detect language and translate to English if needed
        original_lang = detect_language(text)
        english_text, _ = translate_to_english(text, original_lang)
        
        # Verify the text using Llama
        result = verify_text_with_llama(english_text, original_lang)
        
        # Translate results back to original language if needed
        if original_lang != 'en' and MULTILINGUAL_ENABLED:
            result['summary'] = translate_from_english(result['summary'], original_lang)
            result['recommendations'] = [
                translate_from_english(r, original_lang) for r in result['recommendations']
            ]
            for claim in result.get('claims', []):
                if claim.get('explanation'):
                    claim['explanation'] = translate_from_english(claim['explanation'], original_lang)
        
        # Add language info
        result['detected_language'] = original_lang
        result['language_name'] = SUPPORTED_LANGUAGES.get(original_lang, 'Unknown')
        
        # Store in database if user is logged in
        if current_user.is_authenticated:
            history_entry = UserHistory(
                user_id=current_user.id,
                action_type='text_verified',
                action_details=f'Text verification: {result["verdict"]} (score: {result["credibility_score"]}%)',
                article_title=f'Text: {text[:50]}...'
            )
            db.session.add(history_entry)
            db.session.commit()
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in verify_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================
# OCR MEME/QUOTE VERIFICATION (Feature 2B)
# ============================================

def extract_text_from_image(image_bytes):
    """
    Extract text from image using OCR (pytesseract)
    """
    if not OCR_ENABLED:
        return "", "OCR not available"
    
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return "", "Failed to decode image"
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding for better OCR
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Apply dilation to connect text regions
        kernel = np.ones((1, 1), np.uint8)
        gray = cv2.dilate(gray, kernel, iterations=1)
        
        # Convert to PIL Image for pytesseract
        pil_image = Image.fromarray(gray)
        
        # Extract text using pytesseract
        # Support English, Hindi, and Marathi
        text = pytesseract.image_to_string(pil_image, lang='eng+hin+mar')
        
        return text.strip(), None
        
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return "", str(e)

@app.route('/verify_meme', methods=['POST'])
def verify_meme():
    """
    API endpoint to verify memes/quote images
    1. Extract text using OCR
    2. Verify the extracted text using Llama
    """
    try:
        if not OCR_ENABLED:
            return jsonify({
                'error': 'OCR not available. Please install pytesseract and opencv.',
                'ocr_enabled': False
            }), 400
        
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Extract text from image
        extracted_text, ocr_error = extract_text_from_image(image_bytes)
        
        if ocr_error:
            return jsonify({
                'error': f'OCR failed: {ocr_error}',
                'extracted_text': ''
            }), 500
        
        if not extracted_text or len(extracted_text) < 10:
            return jsonify({
                'error': 'No readable text found in image',
                'extracted_text': extracted_text,
                'message': 'The image does not contain enough readable text for verification'
            }), 400
        
        # Detect language of extracted text
        original_lang = detect_language(extracted_text)
        english_text, _ = translate_to_english(extracted_text, original_lang)
        
        # Verify the extracted text
        verification_result = verify_text_with_llama(english_text, original_lang)
        
        # Translate results back if needed
        if original_lang != 'en' and MULTILINGUAL_ENABLED:
            verification_result['summary'] = translate_from_english(
                verification_result['summary'], original_lang
            )
        
        # Add OCR-specific info to result
        verification_result['extracted_text'] = extracted_text
        verification_result['detected_language'] = original_lang
        verification_result['language_name'] = SUPPORTED_LANGUAGES.get(original_lang, 'Unknown')
        verification_result['ocr_enabled'] = True
        verification_result['content_type'] = 'meme/quote_image'
        
        # Store in database if user is logged in
        if current_user.is_authenticated:
            filename = secure_filename(image_file.filename)
            history_entry = UserHistory(
                user_id=current_user.id,
                action_type='meme_verified',
                action_details=f'Meme verification: {verification_result["verdict"]} (score: {verification_result["credibility_score"]}%)',
                article_title=f'Meme: {filename}'
            )
            db.session.add(history_entry)
            db.session.commit()
        
        return jsonify(verification_result), 200
        
    except Exception as e:
        print(f"Error in verify_meme: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Image Detection Routes
@app.route('/image-detection')
def image_detection():
    try:
        return render_template('image_detection.html', active_page='image-detection')
    except Exception as e:
        print(f"Error rendering image detection page: {str(e)}")
        return redirect('/')

@app.route('/detect_image', methods=['POST'])
def detect_image():
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WEBP)'}), 400
        
        # Initialize image detector with SightEngine API
        api_user = getattr(Config, 'SIGHTENGINE_API_USER', None)
        api_secret = getattr(Config, 'SIGHTENGINE_API_SECRET', None)
        detector = ImageDetector(api_user=api_user, api_secret=api_secret)
        
        # Detect AI-generated image
        detection_result = detector.detect_ai_image(image_file)
        
        # Analyze artifacts
        image_file.seek(0)  # Reset file pointer
        artifacts = analyze_image_artifacts(image_file)
        
        # Add artifacts to result
        detection_result['artifacts'] = artifacts
        
        # Store result in database if user is logged in
        if current_user.is_authenticated:
            filename = secure_filename(image_file.filename)
            
            detection_record = ImageDetectionResult(
                user_id=current_user.id,
                image_filename=filename,
                is_ai_generated=detection_result['is_ai_generated'],
                confidence_score=detection_result['confidence'],
                status=detection_result['status']
            )
            
            detection_record.set_reasons(detection_result['reasons'])
            detection_record.set_artifacts(artifacts)
            
            db.session.add(detection_record)
            
            # Add to user history
            history_entry = UserHistory(
                user_id=current_user.id,
                action_type='image_detected',
                action_details=f'Image detection: {detection_result["status"]} (confidence: {detection_result["confidence"]}%)',
                article_title=f'Image: {filename}'
            )
            db.session.add(history_entry)
            db.session.commit()
        
        return jsonify(detection_result), 200
        
    except Exception as e:
        print(f"Error in detect_image endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to process image',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
