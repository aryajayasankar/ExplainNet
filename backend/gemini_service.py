import google.generativeai as genai
import os
import json
from typing import Dict, Optional

# Primary Gemini API key (for YouTube: transcripts, comments, video sentiment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Secondary Gemini API key (for News articles: summaries only)
# If not set, will fall back to primary key
GEMINI_API_KEY_NEWS = os.getenv("GEMINI_API_KEY_NEWS", GEMINI_API_KEY)

# Configure primary API key as default
genai.configure(api_key=GEMINI_API_KEY)

# Candidate models to try (use the first that responds to generation)
_GEMINI_CANDIDATES = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-pro-latest",
    "models/gemini-2.5-flash-lite",
]

# Cached chosen model name (resolved at runtime on first use)
_SELECTED_GEMINI_MODEL = None


def _get_working_model(timeout_seconds: int = 8) -> str:
    """Return the first working Gemini model name from candidates.

    Tries each candidate with a very small generate_content call. Caches result.
    If none work, returns None.
    """
    global _SELECTED_GEMINI_MODEL
    if _SELECTED_GEMINI_MODEL:
        return _SELECTED_GEMINI_MODEL

    if not GEMINI_API_KEY:
        return None

    test_prompt = "Please respond in one word: OK"
    for candidate in _GEMINI_CANDIDATES:
        try:
            model = genai.GenerativeModel(candidate)
            # small test call
            resp = model.generate_content(test_prompt)
            text = getattr(resp, "text", None) or str(resp)
            if text:
                _SELECTED_GEMINI_MODEL = candidate
                print(f"✓ Gemini model selected: {_SELECTED_GEMINI_MODEL}")
                return _SELECTED_GEMINI_MODEL
        except Exception as e:
            # try next candidate
            print(f"Model {candidate} not available: {e}")
            continue

    # None worked
    print("❌ No working Gemini model found for provided API key.")
    return None


async def analyze_sentiment_advanced(text: str, title: str = "") -> Dict:
    """
    Analyze sentiment using Google Gemini AI with advanced insights
    
    Args:
        text: Transcript text to analyze
        title: Video title for context
    
    Returns:
        Dict with sentiment, emotional tone, bias analysis, and more
    """
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Truncate text if too long (Gemini has token limits)
    text = text[:8000]
    
    prompt = f"""
Analyze the sentiment and content of this video transcript. Provide a strict JSON response (no surrounding text).

Video Title: {title}

Transcript:
{text}

Return ONLY valid JSON with the following fields:
{{
  "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED",
  "confidence": 0.0-1.0,
  "positive_score": 0.0-1.0,
  "negative_score": 0.0-1.0,
  "neutral_score": 0.0-1.0,
  "sarcasm_score": 0.0-1.0,
  "emotional_tone": "string",
  "emotions": {{
    "joy": 0-100,
    "sadness": 0-100,
    "anger": 0-100,
    "fear": 0-100,
    "surprise": 0-100,
    "disgust": 0-100
  }},
  "justification": "short explanation (1-2 sentences)",
  "objectivity_score": 0-10,
  "bias_level": "None|Low|Medium|High",
  "bias_type": "string",
  "controversy_level": "None|Low|Medium|High",
  "evidence_quality": "Low|Medium|High",
  "key_themes": ["theme1","theme2"],
  "neutral_summary": "short objective summary"
}}

IMPORTANT: If you include markdown code fences, the content inside MUST be pure JSON. Do not include any non-JSON text outside the JSON.
Ensure numeric fields are numbers and lists are JSON arrays.
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            raise ValueError("No working Gemini model available for this API key")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        # Robust parsing: strip markdown fences, extract JSON block between first '{' and last '}'
        response_text = getattr(response, "text", "") or str(response)
        response_text = response_text.strip()

        # Remove common markdown fences
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        # Attempt to extract the JSON object from any surrounding text
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = response_text[first_brace:last_brace+1]
        else:
            json_text = response_text

        # Final cleanup
        json_text = json_text.strip()

        # Parse JSON
        parsed = json.loads(json_text)

        # Normalize fields and types
        result = {}
        result["model_name"] = "gemini"
        # Helper to coerce numeric fields
        def _num(k, default=0.0):
            v = parsed.get(k, default)
            try:
                return float(v)
            except Exception:
                return default

        def _int(k, default=0):
            v = parsed.get(k, default)
            try:
                return int(v)
            except Exception:
                try:
                    return int(float(v))
                except Exception:
                    return default

        # If the model did not provide a sentiment field, leave it as None
        result["sentiment"] = parsed.get("sentiment") if parsed.get("sentiment") else None
        result["confidence"] = _num("confidence", 0.0)
        result["positive_score"] = _num("positive_score", 0.0)
        result["negative_score"] = _num("negative_score", 0.0)
        result["neutral_score"] = _num("neutral_score", 0.0)
        result["sarcasm_score"] = _num("sarcasm_score", 0.0)
        result["emotional_tone"] = parsed.get("emotional_tone", "")
        
        # Parse emotions object
        emotions_raw = parsed.get("emotions", {})
        if isinstance(emotions_raw, dict):
            emotions_dict = {
                "joy": int(emotions_raw.get("joy", 0)) if isinstance(emotions_raw.get("joy"), (int, float, str)) and str(emotions_raw.get("joy")).replace('.','').isdigit() else 0,
                "sadness": int(emotions_raw.get("sadness", 0)) if isinstance(emotions_raw.get("sadness"), (int, float, str)) and str(emotions_raw.get("sadness")).replace('.','').isdigit() else 0,
                "anger": int(emotions_raw.get("anger", 0)) if isinstance(emotions_raw.get("anger"), (int, float, str)) and str(emotions_raw.get("anger")).replace('.','').isdigit() else 0,
                "fear": int(emotions_raw.get("fear", 0)) if isinstance(emotions_raw.get("fear"), (int, float, str)) and str(emotions_raw.get("fear")).replace('.','').isdigit() else 0,
                "surprise": int(emotions_raw.get("surprise", 0)) if isinstance(emotions_raw.get("surprise"), (int, float, str)) and str(emotions_raw.get("surprise")).replace('.','').isdigit() else 0,
                "disgust": int(emotions_raw.get("disgust", 0)) if isinstance(emotions_raw.get("disgust"), (int, float, str)) and str(emotions_raw.get("disgust")).replace('.','').isdigit() else 0
            }
            result["emotions"] = json.dumps(emotions_dict)
        else:
            result["emotions"] = json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0})
        
        result["justification"] = parsed.get("justification", "")
        result["objectivity_score"] = _int("objectivity_score", 0)
        result["bias_level"] = parsed.get("bias_level", "Unknown")
        result["bias_type"] = parsed.get("bias_type", "")
        result["controversy_level"] = parsed.get("controversy_level", "Unknown")
        result["evidence_quality"] = parsed.get("evidence_quality", "Unknown")

        # key_themes: keep as JSON string for DB compatibility
        kt = parsed.get("key_themes", parsed.get("themes", []))
        if isinstance(kt, list):
            result["key_themes"] = json.dumps(kt)
        else:
            try:
                # It might already be a JSON string
                _parsed = json.loads(kt) if isinstance(kt, str) else kt
                result["key_themes"] = json.dumps(_parsed)
            except Exception:
                result["key_themes"] = json.dumps([])

        result["neutral_summary"] = parsed.get("neutral_summary", parsed.get("summary", ""))

        return result
    
    except Exception as e:
        # Log the error for debugging
        print(f"❌ Gemini sentiment analysis error: {str(e)}")
        # Return structured failure info; sentiment set to None so callers don't treat it as a real 'NEUTRAL'
        return {
            "model_name": "gemini",
            "sentiment": None,
            "confidence": 0.0,
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "emotional_tone": "error",
            "emotions": json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0}),
            "objectivity_score": 0.0,
            "bias_level": "Unknown",
            "bias_type": "error",
            "controversy_level": "Unknown",
            "evidence_quality": "Unknown",
            "key_themes": json.dumps([]),
            "neutral_summary": f"Error analyzing content: {str(e)}",
            "error": str(e),
            "justification": f"Gemini failed to produce sentiment: {str(e)}"
        }


async def analyze_comment_sentiment(comment_text: str) -> Dict:
    """Analyze sentiment of a single comment"""
    
    if not GEMINI_API_KEY:
        return {
            "sentiment": None,
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "toxicity_score": 0.0,
            "emotions": json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0}),
            "justification": "No GEMINI_API_KEY configured"
        }
    
    prompt = f"""
Analyze this YouTube comment and provide sentiment analysis in JSON format:

Comment: {comment_text}

Provide JSON response:
{{
    "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
    "sentiment_score": -1.0 to +1.0,
    "confidence": 0.0-1.0,
    "toxicity_score": 0.0-1.0,
    "emotions": {{
        "joy": 0-100,
        "sadness": 0-100,
        "anger": 0-100,
        "fear": 0-100,
        "surprise": 0-100,
        "disgust": 0-100
    }}
}}
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            return {
                "sentiment": None,
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "toxicity_score": 0.0,
                "emotions": json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0}),
                "justification": "No working Gemini model available"
            }
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = getattr(response, "text", "") or str(response)
        response_text = response_text.strip()

        # Strip fences
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        # Extract JSON block
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = response_text[first_brace:last_brace+1]
        else:
            json_text = response_text

        parsed = json.loads(json_text)

        # Normalize expected numeric fields
        if "sentiment_score" in parsed:
            try:
                parsed["sentiment_score"] = float(parsed["sentiment_score"])
            except Exception:
                parsed["sentiment_score"] = 0.0
        if "confidence" in parsed:
            try:
                parsed["confidence"] = float(parsed["confidence"])
            except Exception:
                parsed["confidence"] = 0.0
        
        # Parse emotions
        emotions_raw = parsed.get("emotions", {})
        if isinstance(emotions_raw, dict):
            try:
                emotions_dict = {
                    "joy": int(float(emotions_raw.get("joy", 0))),
                    "sadness": int(float(emotions_raw.get("sadness", 0))),
                    "anger": int(float(emotions_raw.get("anger", 0))),
                    "fear": int(float(emotions_raw.get("fear", 0))),
                    "surprise": int(float(emotions_raw.get("surprise", 0))),
                    "disgust": int(float(emotions_raw.get("disgust", 0)))
                }
                parsed["emotions"] = json.dumps(emotions_dict)
            except Exception:
                parsed["emotions"] = json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0})
        else:
            parsed["emotions"] = json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0})

        return parsed
    
    except Exception as e:
        return {
            "sentiment": None,
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "toxicity_score": 0.0,
            "emotions": json.dumps({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "surprise": 0, "disgust": 0}),
            "error": str(e),
            "justification": "Gemini comment sentiment failed"
        }


async def summarize_article(title: str, description: str, content: str = "", use_news_key: bool = True) -> Dict:
    """
    Generate a short gist/summary of a news article using Gemini (NO sentiment analysis)
    
    Args:
        title: Article title
        description: Article description/snippet
        content: Full article content (optional, may be truncated)
        use_news_key: If True, use GEMINI_API_KEY_NEWS (default); if False, use primary key
    
    Returns:
        Dict with summary gist only
    """
    
    # Use news API key if available and requested, otherwise use primary key
    api_key = GEMINI_API_KEY_NEWS if use_news_key else GEMINI_API_KEY
    
    if not api_key:
        return {
            "gist": "Gemini API key not configured",
            "error": "No API key"
        }
    
    # Temporarily reconfigure genai with the appropriate key
    original_key = genai.api_key if hasattr(genai, 'api_key') else None
    genai.configure(api_key=api_key)
    
    # Combine available text
    combined_text = f"Title: {title}\n\n"
    if description:
        combined_text += f"Description: {description}\n\n"
    if content:
        combined_text += f"Content: {content[:3000]}"  # Limit content length
    
    prompt = f"""
Provide a very short, objective summary (gist) of this news article in 2-3 sentences. Tell the reader what they can expect from this article.

{combined_text}

Return ONLY a JSON object:
{{
    "gist": "2-3 sentence objective summary here"
}}

Do not include sentiment analysis. Just summarize what the article is about.
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            return {
                "gist": "No working Gemini model available",
                "error": "Model unavailable"
            }
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = getattr(response, "text", "") or str(response)
        response_text = response_text.strip()
        
        # Strip markdown fences
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # Extract JSON block
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = response_text[first_brace:last_brace+1]
        else:
            json_text = response_text
        
        parsed = json.loads(json_text)
        gist_result = {
            "gist": parsed.get("gist", "Summary unavailable")
        }
        
        # Restore original API key if it was changed
        if original_key and original_key != api_key:
            genai.configure(api_key=original_key)
        
        return gist_result
    
    except Exception as e:
        # Restore original API key on error too
        if original_key and original_key != api_key:
            genai.configure(api_key=original_key)
        
        print(f"❌ Gemini article summary error: {str(e)}")
        return {
            "gist": f"Error generating summary: {str(e)}",
            "error": str(e)
        }


async def extract_entities(text: str, context: str = "") -> Dict:
    """
    Extract named entities from text using Gemini
    
    Args:
        text: Text to extract entities from (transcript or article)
        context: Additional context (e.g., video title, article headline)
    
    Returns:
        Dict with lists of persons, organizations, locations, and other entities
    """
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    # Truncate text if too long
    text = text[:10000]
    
    prompt = f"""
Extract all named entities from this text. Return a JSON object with categorized entities.

Context: {context}

Text:
{text}

Return JSON in this exact format:
{{
    "persons": ["person1", "person2"],
    "organizations": ["org1", "org2"],
    "locations": ["location1", "location2"],
    "products": ["product1"],
    "events": ["event1"],
    "other": ["other1"]
}}

Rules:
- Include full names (e.g., "Elon Musk" not just "Musk")
- Remove duplicates
- Return empty arrays if no entities found
- Maximum 20 entities per category
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            raise ValueError("No working Gemini model available for this API key")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Clean markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        entities = json.loads(response_text.strip())
        
        # Ensure all required keys exist
        default_entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "products": [],
            "events": [],
            "other": []
        }
        default_entities.update(entities)
        
        return default_entities
    
    except Exception as e:
        print(f"Entity extraction error: {str(e)}")
        return {
            "persons": [],
            "organizations": [],
            "locations": [],
            "products": [],
            "events": [],
            "other": []
        }


async def calculate_news_relevance(topic_name: str, article_title: str) -> int:
    """
    Calculate how closely a news article title relates to the user's topic.
    
    Args:
        topic_name: The user's topic query
        article_title: The news article title
    
    Returns:
        Relevance score from 0-100
    """
    
    if not GEMINI_API_KEY:
        return 50  # Default middling score if no API
    
    prompt = f"""
Rate how closely this news article title relates to the given topic on a scale of 0-100.

Topic: {topic_name}
Article Title: {article_title}

Consider:
- Direct keyword matches (higher score)
- Semantic similarity (related concepts)
- Contextual relevance

Return ONLY a JSON object:
{{
    "relevance_score": 0-100
}}

Return just the number between 0-100.
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            return 50
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = getattr(response, "text", "") or str(response)
        response_text = response_text.strip()
        
        # Strip markdown fences
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # Extract JSON block
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = response_text[first_brace:last_brace+1]
            parsed = json.loads(json_text)
            score = int(parsed.get("relevance_score", 50))
        else:
            # Try to extract just a number
            import re
            numbers = re.findall(r'\d+', response_text)
            score = int(numbers[0]) if numbers else 50
        
        # Clamp to 0-100
        return max(0, min(100, score))
    
    except Exception as e:
        print(f"❌ Relevance scoring error: {str(e)}")
        return 50  # Default middling score on error


async def generate_ai_synthesis(topic_data: Dict) -> Dict:
    """
    Generate comprehensive AI synthesis combining all analytics data.
    
    Args:
        topic_data: Dictionary containing:
            - topic_name: str
            - videos: List of video data with sentiments, impact, emotions, views
            - articles: List of news article data with relevance scores
            - analysis_date: str
    
    Returns:
        Dict with executive_summary, key_trends, surprising_findings, recommendations
    """
    
    if not GEMINI_API_KEY:
        return {
            "executive_summary": "Gemini API not configured",
            "key_trends": [],
            "surprising_findings": [],
            "recommendations": [],
            "error": "No API key"
        }
    
    # Build comprehensive data summary
    topic_name = topic_data.get("topic_name", "Unknown Topic")
    videos = topic_data.get("videos", [])
    articles = topic_data.get("articles", [])
    
    # Calculate aggregate stats
    total_videos = len(videos)
    total_articles = len(articles)
    
    video_sentiments = [v.get("gemini_sentiment") or v.get("hf_sentiment") for v in videos if v.get("gemini_sentiment") or v.get("hf_sentiment")]
    positive_count = sum(1 for s in video_sentiments if s == "POSITIVE")
    negative_count = sum(1 for s in video_sentiments if s == "NEGATIVE")
    neutral_count = sum(1 for s in video_sentiments if s == "NEUTRAL")
    
    avg_impact = sum(v.get("impact_score", 0) for v in videos) / total_videos if total_videos > 0 else 0
    total_views = sum(v.get("view_count", 0) for v in videos)
    
    avg_relevance = sum(a.get("relevance_score", 50) for a in articles) / total_articles if total_articles > 0 else 0
    
    prompt = f"""
You are an expert data analyst. Analyze this comprehensive dataset about "{topic_name}" and provide actionable insights.

DATASET SUMMARY:
- Topic: {topic_name}
- Total YouTube Videos Analyzed: {total_videos}
- Total News Articles: {total_articles}
- Total Views Across Videos: {total_views:,}

VIDEO SENTIMENT BREAKDOWN:
- Positive: {positive_count} ({positive_count/max(total_videos,1)*100:.1f}%)
- Negative: {negative_count} ({negative_count/max(total_videos,1)*100:.1f}%)
- Neutral: {neutral_count} ({neutral_count/max(total_videos,1)*100:.1f}%)

METRICS:
- Average Impact Score: {avg_impact:.2f}/5.0
- Average News Relevance: {avg_relevance:.1f}/100

DETAILED VIDEO DATA:
{json.dumps(videos[:10], indent=2)}

DETAILED ARTICLE DATA:
{json.dumps(articles[:10], indent=2)}

Based on this data, provide a JSON response with:

{{
    "executive_summary": "3-4 sentence overview highlighting the most important finding",
    "key_trends": [
        "Trend 1 with specific numbers",
        "Trend 2 with specific numbers",
        "Trend 3 with specific numbers"
    ],
    "surprising_findings": [
        "Unexpected insight 1",
        "Unexpected insight 2"
    ],
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2",
        "Actionable recommendation 3"
    ],
    "dominant_emotion": "The most prominent emotion detected across content",
    "content_quality_assessment": "Assessment of evidence quality and objectivity"
}}

Be specific, reference actual numbers, and provide genuinely useful insights.
"""
    
    try:
        model_name = _get_working_model()
        if not model_name:
            return {
                "executive_summary": "No working Gemini model available",
                "key_trends": [],
                "surprising_findings": [],
                "recommendations": [],
                "error": "Model unavailable"
            }
        
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = getattr(response, "text", "") or str(response)
        response_text = response_text.strip()
        
        # Strip markdown fences
        if response_text.startswith("```json"):
            response_text = response_text[len("```json"):].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()
        
        # Extract JSON block
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_text = response_text[first_brace:last_brace+1]
        else:
            json_text = response_text
        
        parsed = json.loads(json_text)
        
        # Ensure all fields exist
        result = {
            "executive_summary": parsed.get("executive_summary", "Analysis complete"),
            "key_trends": parsed.get("key_trends", []),
            "surprising_findings": parsed.get("surprising_findings", []),
            "recommendations": parsed.get("recommendations", []),
            "dominant_emotion": parsed.get("dominant_emotion", "Mixed"),
            "content_quality_assessment": parsed.get("content_quality_assessment", "Varied quality")
        }
        
        return result
    
    except Exception as e:
        print(f"❌ AI synthesis error: {str(e)}")
        return {
            "executive_summary": f"Error generating synthesis: {str(e)}",
            "key_trends": [],
            "surprising_findings": [],
            "recommendations": [],
            "error": str(e)
        }
