"""
Open-Source Sentiment Models Setup
===================================
Replaces Gemini with reproducible open-source models.

Models used:
1. RoBERTa (Twitter-trained): cardiffnlp/twitter-roberta-base-sentiment-latest
2. DistilBERT (SST-2): distilbert-base-uncased-finetuned-sst-2-english  
3. Emotion classifier: SamLowe/roberta-base-go_emotions

Usage:
    python 04_setup_models.py
"""

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import json
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / 'models'
MODELS_DIR.mkdir(exist_ok=True)

def check_gpu():
    """Check if GPU is available."""
    if torch.cuda.is_available():
        print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        return 0
    else:
        print("⚠️  GPU not available, using CPU (will be slower)")
        return -1

def download_models():
    """Download and cache all models."""
    device = check_gpu()
    
    models_info = {
        'roberta': {
            'name': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
            'task': 'sentiment-analysis',
            'description': 'RoBERTa trained on Twitter data'
        },
        'distilbert': {
            'name': 'distilbert-base-uncased-finetuned-sst-2-english',
            'task': 'sentiment-analysis',
            'description': 'DistilBERT fine-tuned on SST-2'
        },
        'emotions': {
            'name': 'SamLowe/roberta-base-go_emotions',
            'task': 'text-classification',
            'description': 'RoBERTa for 28 emotion classification'
        }
    }
    
    print("\n" + "="*80)
    print("DOWNLOADING MODELS")
    print("="*80)
    
    downloaded = {}
    
    for key, info in models_info.items():
        print(f"\n📦 {key.upper()}: {info['name']}")
        print(f"   {info['description']}")
        
        try:
            # Download model
            model_pipeline = pipeline(
                info['task'],
                model=info['name'],
                device=device,
                truncation=True,
                max_length=512
            )
            
            downloaded[key] = {
                'model_name': info['name'],
                'status': 'success',
                'device': 'GPU' if device == 0 else 'CPU'
            }
            
            # Test
            test_text = "This is a test sentence for sentiment analysis."
            result = model_pipeline(test_text)
            print(f"   ✅ Downloaded and tested: {result}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            downloaded[key] = {
                'model_name': info['name'],
                'status': 'failed',
                'error': str(e)
            }
    
    # Save model info
    info_file = MODELS_DIR / 'models_info.json'
    with open(info_file, 'w') as f:
        json.dump(downloaded, f, indent=2)
    
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    success_count = sum(1 for v in downloaded.values() if v['status'] == 'success')
    print(f"✅ {success_count}/{len(models_info)} models downloaded successfully")
    print(f"📁 Model info saved to: {info_file}")
    print("="*80)

if __name__ == '__main__':
    download_models()
