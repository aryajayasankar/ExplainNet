from typing import Dict, List
import json

def calculate_video_priority(video: Dict) -> float:
    impact = (video.get('impact_score') or 0) * 20
    return min(100, max(0, impact))

def generate_viewing_path(videos: List[Dict]) -> Dict:
    nodes = [{'id': f"v_{v['id']}", 'priority': calculate_video_priority(v)} for v in videos]
    return {'nodes': nodes, 'edges': [], 'recommendations': []}
