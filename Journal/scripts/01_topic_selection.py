"""
Topic Selection for Research Dataset
=====================================
Selects 25 controversial topics across 5 domains for dataset collection.
"""

RESEARCH_TOPICS = {
    'health': [
        'COVID-19 vaccines efficacy',
        'intermittent fasting benefits',
        'mental health awareness therapy',
        'sleep optimization techniques',
        'dietary supplement safety'
    ],
    'politics': [
        'climate change policy solutions',
        'immigration reform debate',
        'election integrity measures',
        'universal healthcare systems',
        'education funding reform'
    ],
    'technology': [
        'artificial intelligence safety risks',
        'cryptocurrency regulation policy',
        'social media privacy concerns',
        'remote work future trends',
        'electric vehicles adoption'
    ],
    'economics': [
        'inflation impact economy',
        'housing crisis solutions',
        'student debt forgiveness',
        'minimum wage increase',
        'universal basic income'
    ],
    'society': [
        'police reform policies',
        'income inequality solutions',
        'affordable housing crisis',
        'climate activism effectiveness',
        'social justice movements'
    ]
}

def get_all_topics():
    """Returns flat list of all 25 topics."""
    topics = []
    for domain, topic_list in RESEARCH_TOPICS.items():
        topics.extend(topic_list)
    return topics

def get_topics_by_domain(domain):
    """Returns topics for specific domain."""
    return RESEARCH_TOPICS.get(domain, [])

def print_topic_summary():
    """Prints formatted summary of all topics."""
    print("="*80)
    print("RESEARCH DATASET TOPICS (N=25)")
    print("="*80)
    
    for i, (domain, topics) in enumerate(RESEARCH_TOPICS.items(), 1):
        print(f"\n{i}. {domain.upper()} ({len(topics)} topics):")
        for j, topic in enumerate(topics, 1):
            print(f"   {j}. {topic}")
    
    print(f"\nTotal topics: {len(get_all_topics())}")
    print("Expected videos: 125 (5 per topic)")
    print("Expected news articles: 250+ (10 per topic)")
    print("="*80)

if __name__ == '__main__':
    print_topic_summary()
