"""
VADER Sentiment Analysis Service
Free, local sentiment analysis - no API calls needed!
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict

# Initialize VADER analyzer (runs locally, completely free)
_vader_analyzer = None

def _get_analyzer():
    """Lazy initialization of VADER analyzer"""
    global _vader_analyzer
    if _vader_analyzer is None:
        _vader_analyzer = SentimentIntensityAnalyzer()
    return _vader_analyzer


async def analyze_sentiment(text: str) -> Dict:
    """
    Analyze sentiment using VADER (Valence Aware Dictionary and sEntiment Reasoner)
    
    VADER is perfect for social media text, completely free, and runs locally.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dict with sentiment, confidence, and score breakdown
    """
    
    try:
        # Truncate text to reasonable length
        text = text[:5000]
        
        # Get VADER analyzer
        analyzer = _get_analyzer()
        
        # Analyze sentiment
        scores = analyzer.polarity_scores(text)
        
        # VADER returns: neg, neu, pos, compound (-1 to 1)
        positive_score = scores['pos']
        neutral_score = scores['neu']
        negative_score = scores['neg']
        compound = scores['compound']  # Overall sentiment score
        
        # Determine sentiment based on compound score
        # VADER threshold: >= 0.05 positive, <= -0.05 negative, else neutral
        if compound >= 0.05:
            sentiment = 'POSITIVE'
            confidence = positive_score
        elif compound <= -0.05:
            sentiment = 'NEGATIVE'
            confidence = negative_score
        else:
            sentiment = 'NEUTRAL'
            confidence = neutral_score
        
        return {
            'model_name': 'vader',
            'sentiment': sentiment,
            'confidence': round(float(confidence), 3),
            'positive_score': round(float(positive_score), 3),
            'negative_score': round(float(negative_score), 3),
            'neutral_score': round(float(neutral_score), 3),
            'justification': f"VADER analyzed sentiment as {sentiment} (compound: {compound:.3f})"
        }
    
    except Exception as e:
        # If VADER fails for any reason, return structured error
        return {
            "model_name": "vader",
            "sentiment": None,
            "confidence": 0.0,
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "justification": f"VADER error: {str(e)}"
        }
