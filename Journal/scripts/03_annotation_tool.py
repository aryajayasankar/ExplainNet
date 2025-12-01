"""
Manual Annotation Tool
======================
Interactive CLI tool for annotating videos with sentiment, emotions, and credibility.

Usage:
    python 03_annotation_tool.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_FILE = DATA_DIR / 'research_dataset_raw.json'
ANNOTATED_FILE = DATA_DIR / 'research_dataset_annotated.json'

SENTIMENT_MAP = {
    '1': 'VERY_NEGATIVE',
    '2': 'NEGATIVE',
    '3': 'NEUTRAL',
    '4': 'POSITIVE',
    '5': 'VERY_POSITIVE',
    '6': 'MIXED'
}

CREDIBILITY_MAP = {
    '1': 'LOW',
    '2': 'MEDIUM',
    '3': 'HIGH'
}

def load_dataset():
    """Load the raw dataset."""
    if not RAW_FILE.exists():
        print(f"❌ Error: {RAW_FILE} not found")
        print("Run 02_data_collection.py first")
        sys.exit(1)
    
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_dataset(data):
    """Save annotated dataset."""
    with open(ANNOTATED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_emotion_input(emotion_name):
    """Get emotion score with validation."""
    while True:
        try:
            score = int(input(f"  {emotion_name.capitalize():12} (0-100): "))
            if 0 <= score <= 100:
                return score
            print("    ⚠️  Must be between 0-100")
        except ValueError:
            print("    ⚠️  Enter a number")

def annotate_video(video, video_num, total_videos, topic_name, domain):
    """
    Annotate a single video interactively.
    """
    print("\n" + "="*80)
    print(f"VIDEO {video_num}/{total_videos}")
    print("="*80)
    print(f"Topic:   {topic_name}")
    print(f"Domain:  {domain}")
    print(f"Title:   {video['title']}")
    print(f"Channel: {video.get('channel_title', 'N/A')}")
    print(f"Views:   {video.get('view_count', 0):,}")
    print(f"\nTranscript preview (first 500 chars):")
    print("-"*80)
    transcript = video.get('transcript', '')
    print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
    print("-"*80)
    
    # Show current predictions if available
    if video.get('emotions_json'):
        print(f"\nCurrent system predictions (for reference):")
        print(f"  Emotions: {video['emotions_json']}")
    
    print("\n" + "="*80)
    print("ANNOTATION")
    print("="*80)
    
    # Sentiment
    print("\nSentiment (1=Very Negative, 2=Negative, 3=Neutral, 4=Positive, 5=Very Positive, 6=Mixed):")
    while True:
        choice = input("Enter 1-6: ").strip()
        if choice in SENTIMENT_MAP:
            video['ground_truth_sentiment'] = SENTIMENT_MAP[choice]
            break
        print("⚠️  Invalid choice. Enter 1-6")
    
    # Emotions
    print("\nEmotions (rate each 0-100):")
    emotions = {}
    for emotion in ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']:
        emotions[emotion] = get_emotion_input(emotion)
    video['ground_truth_emotions'] = emotions
    
    # Credibility
    print("\nCredibility (1=Low, 2=Medium, 3=High):")
    while True:
        choice = input("Enter 1-3: ").strip()
        if choice in CREDIBILITY_MAP:
            video['credibility_label'] = CREDIBILITY_MAP[choice]
            break
        print("⚠️  Invalid choice. Enter 1-3")
    
    # Misinformation
    print("\nMisinformation flag (contains obvious false claims)?")
    while True:
        choice = input("Enter Y/N: ").strip().upper()
        if choice in ['Y', 'N']:
            video['misinformation_flag'] = (choice == 'Y')
            break
        print("⚠️  Invalid choice. Enter Y or N")
    
    # Metadata
    video['annotation_date'] = datetime.now().isoformat()
    video['annotator'] = 'self'
    
    return video

def show_progress(data):
    """Show annotation progress statistics."""
    total_videos = sum(len(topic['videos']) for topic in data['topics'])
    annotated = sum(
        1 for topic in data['topics'] 
        for video in topic['videos'] 
        if video.get('ground_truth_sentiment') is not None
    )
    
    print("\n" + "="*80)
    print("PROGRESS SUMMARY")
    print("="*80)
    print(f"Total videos: {total_videos}")
    print(f"Annotated:    {annotated}")
    print(f"Remaining:    {total_videos - annotated}")
    print(f"Progress:     {annotated/total_videos*100:.1f}%")
    
    # Progress by domain
    domain_stats = defaultdict(lambda: {'total': 0, 'done': 0})
    for topic in data['topics']:
        domain = topic['domain']
        for video in topic['videos']:
            domain_stats[domain]['total'] += 1
            if video.get('ground_truth_sentiment'):
                domain_stats[domain]['done'] += 1
    
    print("\nProgress by domain:")
    for domain, stats in sorted(domain_stats.items()):
        pct = stats['done']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"  {domain:12}: {stats['done']:3}/{stats['total']:3} ({pct:5.1f}%)")
    
    print("="*80)

def main():
    """Main annotation loop."""
    print("\n" + "="*80)
    print("VIDEO ANNOTATION TOOL")
    print("="*80)
    print("\nRead ANNOTATION_GUIDELINES.md before starting!")
    print("Press Ctrl+C at any time to save and quit")
    print("\nLoading dataset...")
    
    data = load_dataset()
    
    # Flatten videos for easier iteration
    video_list = []
    for topic in data['topics']:
        for video in topic['videos']:
            video_list.append({
                'video': video,
                'topic_name': topic['topic_name'],
                'domain': topic['domain']
            })
    
    # Filter unannotated
    to_annotate = [
        item for item in video_list 
        if item['video'].get('ground_truth_sentiment') is None
    ]
    
    if not to_annotate:
        print("\n✅ All videos are already annotated!")
        show_progress(data)
        return
    
    print(f"\nVideos to annotate: {len(to_annotate)}")
    show_progress(data)
    
    input("\nPress Enter to start annotating...")
    
    try:
        for i, item in enumerate(to_annotate, 1):
            annotate_video(
                item['video'],
                i,
                len(to_annotate),
                item['topic_name'],
                item['domain']
            )
            
            # Save after each annotation
            save_dataset(data)
            
            print(f"\n✅ Saved ({i}/{len(to_annotate)} completed)")
            
            # Show progress every 10 videos
            if i % 10 == 0:
                show_progress(data)
                if i < len(to_annotate):
                    cont = input("\nContinue? (Y/N): ").strip().upper()
                    if cont != 'Y':
                        break
        
        print("\n" + "="*80)
        print("ANNOTATION COMPLETE!")
        print("="*80)
        show_progress(data)
        print(f"\nAnnotated dataset saved to: {ANNOTATED_FILE}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        save_dataset(data)
        print(f"✅ Progress saved to: {ANNOTATED_FILE}")
        show_progress(data)

if __name__ == '__main__':
    main()
