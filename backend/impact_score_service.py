import math
from datetime import datetime, timezone
from typing import Dict


def calculate_impact_score(video_data: Dict, sentiment_data: Dict = None) -> Dict:
    """
    Calculate comprehensive impact score with 5 components + recency boost
    
    Components:
    1. Reach Score (25%) - Based on views and subscriber count
    2. Engagement Score (30%) - Based on likes/comments ratio
    3. Sentiment Score (20%) - Based on sentiment analysis (0 if no sentiment data)
    4. Quality Score (15%) - Based on HF+Gemini agreement (0 if no sentiment data)
    5. Influence Score (10%) - Based on channel metrics
    
    Plus: Recency Boost multiplier
    
    Returns:
        Dict with all score components and final impact score (0-10)
    """
    
    # Extract data
    views = video_data.get("view_count", 0)
    likes = video_data.get("like_count", 0)
    comments = video_data.get("comment_count", 0)
    subscribers = video_data.get("subscriber_count", 0)
    published_at = video_data.get("published_at")
    
    # Handle None sentiment_data gracefully
    if sentiment_data is None:
        hf_sentiment = {}
        gemini_sentiment = {}
    else:
        hf_sentiment = sentiment_data.get("huggingface", {})
        gemini_sentiment = sentiment_data.get("gemini", {})
    
    # 1. REACH SCORE (0-10) - Logarithmic scale for views
    if views > 0:
        # log10 scale: 1k=3, 10k=4, 100k=5, 1M=6, 10M=7
        reach_score = min(10, (math.log10(views + 1) / 7) * 10)
    else:
        reach_score = 0
    
    # 2. ENGAGEMENT SCORE (0-10) - Likes and comments ratio
    if views > 0:
        like_rate = likes / views
        comment_rate = comments / views
        
        # Normalize: 5% like rate = 5 points, 1% comment rate = 5 points
        like_component = min(5, like_rate * 100)
        comment_component = min(5, comment_rate * 100)
        
        engagement_score = like_component + comment_component
    else:
        engagement_score = 0
    
    # 3. SENTIMENT SCORE (0-10) - Map sentiment to score
    sentiment_score = map_sentiment_to_score(hf_sentiment, gemini_sentiment)
    
    # 4. QUALITY SCORE (0-10) - Agreement between models
    quality_score = calculate_quality_score(hf_sentiment, gemini_sentiment)
    
    # 5. INFLUENCE SCORE (0-10) - Channel authority
    if subscribers > 0:
        # log10 scale: 1k=3, 10k=4, 100k=5, 1M=6, 10M=7
        influence_score = min(10, (math.log10(subscribers + 1) / 7) * 10)
    else:
        influence_score = 0
    
    # WEIGHTED AVERAGE
    base_impact = (
        reach_score * 0.25 +
        engagement_score * 0.30 +
        sentiment_score * 0.20 +
        quality_score * 0.15 +
        influence_score * 0.10
    )
    
    # RECENCY BOOST (1.0x to 1.5x)
    recency_boost = calculate_recency_boost(published_at)
    
    # FINAL IMPACT SCORE (capped at 10)
    final_impact = min(10, base_impact * recency_boost)
    
    return {
        "impact_score": round(final_impact, 1),
        "reach_score": round(reach_score, 1),
        "engagement_score": round(engagement_score, 1),
        "sentiment_score": round(sentiment_score, 1),
        "quality_score": round(quality_score, 1),
        "influence_score": round(influence_score, 1),
        "recency_boost": round(recency_boost, 2)
    }


def map_sentiment_to_score(hf_sentiment: Dict, gemini_sentiment: Dict) -> float:
    """Map sentiment to 0-10 score (higher = more positive)"""
    
    # Return 0 if no sentiment data available
    if not hf_sentiment and not gemini_sentiment:
        return 0.0
    
    # Average confidence from both models
    hf_conf = hf_sentiment.get("confidence", 0.5) if hf_sentiment else 0.0
    gemini_conf = gemini_sentiment.get("confidence", 0.5) if gemini_sentiment else 0.0
    
    # Handle case where only one model has data
    if not hf_sentiment:
        avg_confidence = gemini_conf
    elif not gemini_sentiment:
        avg_confidence = hf_conf
    else:
        avg_confidence = (hf_conf + gemini_conf) / 2
    
    # Get sentiment types
    # Use None when a model did not return a sentiment rather than defaulting to NEUTRAL
    hf_sent = hf_sentiment.get("sentiment") if hf_sentiment and hf_sentiment.get("sentiment") else None
    gemini_sent = gemini_sentiment.get("sentiment") if gemini_sentiment and gemini_sentiment.get("sentiment") else None
    
    # Map to numerical values
    sentiment_values = {
        "POSITIVE": 8,
        "NEGATIVE": 2,
        "MIXED": 5,
        # If a model explicitly says NEUTRAL we treat it as a middle value, but missing models are skipped
        "NEUTRAL": 5
    }

    values = []
    if hf_sent is not None:
        values.append(sentiment_values.get(hf_sent, 5))
    if gemini_sent is not None:
        values.append(sentiment_values.get(gemini_sent, 5))

    # If no model provided a sentiment, return 0
    if not values:
        return 0.0

    # Average value from available models
    avg_value = sum(values) / len(values)

    score = avg_value * avg_confidence

    return min(10, max(0, score))


def calculate_quality_score(hf_sentiment: Dict, gemini_sentiment: Dict) -> float:
    """Calculate quality based on model agreement and confidence"""
    
    # Return 0 if no sentiment data available
    if not hf_sentiment and not gemini_sentiment:
        return 0.0
    
    # Use None for missing sentiments
    hf_sent = hf_sentiment.get("sentiment") if hf_sentiment and hf_sentiment.get("sentiment") else None
    gemini_sent = gemini_sentiment.get("sentiment") if gemini_sentiment and gemini_sentiment.get("sentiment") else None

    hf_conf = hf_sentiment.get("confidence", 0.5) if hf_sentiment else 0.0
    gemini_conf = gemini_sentiment.get("confidence", 0.5) if gemini_sentiment else 0.0
    
    # Agreement bonus
    if hf_sent is None and gemini_sent is None:
        agreement_score = 0
    elif hf_sent is None or gemini_sent is None:
        # Only one model present => partial agreement
        agreement_score = 4
    elif hf_sent == gemini_sent:
        agreement_score = 7  # High base for agreement
    else:
        agreement_score = 3  # Lower for disagreement
    
    # Average confidence bonus (0-3 points)
    if not hf_sentiment and not gemini_sentiment:
        avg_confidence = 0.0
    elif not hf_sentiment:
        avg_confidence = gemini_conf
    elif not gemini_sentiment:
        avg_confidence = hf_conf
    else:
        avg_confidence = (hf_conf + gemini_conf) / 2
    
    confidence_bonus = avg_confidence * 3
    
    total = agreement_score + confidence_bonus
    return min(10, total)


def calculate_recency_boost(published_at) -> float:
    """
    Calculate recency boost multiplier
    - Last 7 days: 1.5x
    - Last 30 days: 1.3x
    - Last 90 days: 1.1x
    - Older: 1.0x
    """
    
    if not published_at:
        return 1.0
    
    # Parse published date
    if isinstance(published_at, str):
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except:
            return 1.0
    else:
        pub_date = published_at
    
    # Make sure both datetimes are timezone-aware
    if pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    days_old = (now - pub_date).days
    
    if days_old <= 7:
        return 1.5
    elif days_old <= 30:
        return 1.3
    elif days_old <= 90:
        return 1.1
    else:
        return 1.0


def determine_overall_sentiment(hf_sentiment: Dict, gemini_sentiment: Dict) -> tuple:
    """
    Determine overall sentiment and agreement status
    
    Returns:
        (overall_sentiment, models_agree)
    """
    
    # Extract sentiments (may be None when a model failed or returned no label)
    hf_sent = hf_sentiment.get("sentiment") if hf_sentiment and hf_sentiment.get("sentiment") else None
    gemini_sent = gemini_sentiment.get("sentiment") if gemini_sentiment and gemini_sentiment.get("sentiment") else None

    # Normalize strings to uppercase for comparison
    hf_sent_u = hf_sent.upper() if isinstance(hf_sent, str) else None
    gemini_sent_u = gemini_sent.upper() if isinstance(gemini_sent, str) else None

    # If both models returned nothing, overall is None
    if hf_sent_u is None and gemini_sent_u is None:
        return None, False

    # If both provided the same label, they agree
    if hf_sent_u is not None and hf_sent_u == gemini_sent_u:
        return hf_sent_u, True

    # If only one model provided a label, use that label (no agreement)
    if hf_sent_u is None and gemini_sent_u is not None:
        return gemini_sent_u, False
    if gemini_sent_u is None and hf_sent_u is not None:
        return hf_sent_u, False

    # Both provided different labels: pick the one with higher confidence
    hf_conf = hf_sentiment.get("confidence", 0) if hf_sentiment else 0
    gemini_conf = gemini_sentiment.get("confidence", 0) if gemini_sentiment else 0
    if hf_conf >= gemini_conf:
        return hf_sent_u, False
    else:
        return gemini_sent_u, False
