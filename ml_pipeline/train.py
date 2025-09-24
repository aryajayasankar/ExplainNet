import torch
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from sqlalchemy.orm import Session
import numpy as np

from backend.database import SessionLocal
from backend import models
from ml_pipeline.graph_builder import build_graph_for_topic
from ml_pipeline.model import GNN

def calculate_virality_score(videos):
    """Calculates a simple virality score for a set of videos."""
    if not videos:
        return 0

    total_score = 0
    for video in videos:
        # Simple weighted sum, using log to normalize large numbers
        score = np.log(
            1 + 
            (video.view_count or 0) + 
            (video.like_count or 0) * 10 + 
            (video.comment_count or 0) * 20
        )
        total_score += score
    return total_score

def prepare_dataset():
    """Prepares the full dataset of graphs for all topics."""
    print("Preparing dataset...")
    db = SessionLocal()
    topics = db.query(models.Topic).all()
    db.close()

    dataset = []
    for topic in topics:
        print(f"\n--- Processing Topic ID: {topic.topic_id} ({topic.topic_name}) ---")
        graph_data = build_graph_for_topic(topic.topic_id)
        if graph_data:
            # Calculate the virality score for this topic's graph
            db = SessionLocal()
            _, _, videos = get_data_for_topic(db, topic.topic_id)
            db.close()
            virality = calculate_virality_score(videos)

            # Attach the score as the target 'y' for the graph
            graph_data.y = torch.tensor([[virality]], dtype=torch.float)
            dataset.append(graph_data)

    print(f"\nDataset prepared with {len(dataset)} graphs.")
    return dataset

def main():
    # 1. Prepare the dataset
    dataset = prepare_dataset()
    if len(dataset) < 2:
        print("Not enough data to train. Please analyze at least 2 topics.")
        return

    # Use a dataloader to handle batches of graphs
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    # 2. Initialize the Model, Loss Function, and Optimizer
    # The input features will be the size of the 'x' vector in our graph data
    input_feature_size = dataset[0].num_node_features
    model = GNN(in_channels=input_feature_size, hidden_channels=64, out_channels=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.MSELoss() # Mean Squared Error for regression

    # 3. The Training Loop
    print("\n--- Starting Model Training ---")
    model.train()
    for epoch in range(100): # We train for 100 epochs
        total_loss = 0
        for batch in loader:
            optimizer.zero_grad() # Clear gradients

            # Forward pass: predict
            out = model(batch.x, batch.edge_index, batch.batch)

            # Calculate loss
            loss = loss_fn(out, batch.y)

            # Backward pass: compute gradients
            loss.backward()

            # Update model weights
            optimizer.step()
            total_loss += loss.item()

        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d}, Loss: {total_loss/len(loader):.4f}")

    # 4. Save the trained model
    model_path = "gnn_model.pth"
    torch.save(model.state_dict(), model_path)
    print(f"\n--- Training Complete ---")
    print(f"Trained model saved to {model_path}")


# Helper function needed for prepare_dataset
def get_data_for_topic(db: Session, topic_id: int):
    videos = db.query(models.Video).filter(models.Video.topic_id == topic_id).all()
    return None, None, videos

if __name__ == '__main__':
    main()