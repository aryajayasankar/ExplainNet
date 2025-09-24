import torch
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from torch_geometric.data import Data

# This import now works because of the __init__.py file
from backend.database import SessionLocal
from backend import models

# --- 1. DATA QUERYING ---
def get_data_for_topic(db: Session, topic_id: int):
    """Query all relevant data for a given topic ID."""
    topic = db.query(models.Topic).filter(models.Topic.topic_id == topic_id).first()
    if not topic:
        return None, [], []
    articles = db.query(models.Article).filter(models.Article.topic_id == topic_id).all()
    videos = db.query(models.Video).filter(models.Video.topic_id == topic_id).all()
    return topic, articles, videos

# --- 2. GRAPH CONSTRUCTION ---
def build_graph_for_topic(topic_id: int):
    """Builds a PyG Data object for a specific topic."""
    db = SessionLocal()
    topic, articles, videos = get_data_for_topic(db, topic_id)
    db.close()

    if not topic:
        print(f"No data found for topic_id {topic_id}")
        return None

    print("Initializing Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded.")

    node_features = []
    node_map = {}

    print(f"Processing {len(articles)} articles...")
    for article in articles:
        node_map[f"article_{article.article_id}"] = len(node_map)
        embedding = model.encode(article.headline, convert_to_tensor=True)
        features = torch.cat([embedding, torch.tensor([0])]) # 0 for article
        node_features.append(features)

    print(f"Processing {len(videos)} videos...")
    for video in videos:
        node_map[f"video_{video.video_id}"] = len(node_map)
        embedding = model.encode(video.title, convert_to_tensor=True)
        features = torch.cat([embedding, torch.tensor([1])]) # 1 for video
        node_features.append(features)

    x = torch.stack(node_features)
    edge_index = torch.empty((2, 0), dtype=torch.long)

    graph_data = Data(x=x, edge_index=edge_index)
    print("\nGraph constructed successfully!")
    return graph_data

# --- 3. TESTING BLOCK ---
if __name__ == '__main__':
    print("Attempting to build graph for topic_id = 1...")
    graph = build_graph_for_topic(topic_id=1)

    if graph:
        print("\n--- PyTorch Geometric Data Object ---")
        print(graph)
        print(f"Number of nodes: {graph.num_nodes}")
        print(f"Number of features per node: {graph.num_node_features}")
        print(f"Number of edges: {graph.num_edges}")