import torch
from ml_pipeline.model import GNN
from ml_pipeline.graph_builder import build_graph_for_topic

# --- 1. Load the Trained Model ---
# This number MUST match the features created in graph_builder.py (384 + 1 = 385)
MODEL_INPUT_FEATURES = 385 
model = GNN(in_channels=MODEL_INPUT_FEATURES, hidden_channels=64, out_channels=1)

# Load the saved weights from the .pth file
model_path = "gnn_model.pth"
try:
    model.load_state_dict(torch.load(model_path))
    print(f"Trained model loaded successfully from {model_path}")
except FileNotFoundError:
    print(f"Error: Model file not found at {model_path}. Please train the model first.")
    model = None

if model:
    model.eval() # Set the model to evaluation mode

# --- 2. Create the Prediction Function ---
def predict_virality(topic_id: int):
    """
    Builds a graph for a topic and uses the trained GNN to predict its virality.
    """
    if not model:
        raise RuntimeError("Model is not loaded. Cannot make predictions.")

    print(f"Making prediction for topic_id: {topic_id}")
    graph_data = build_graph_for_topic(topic_id)

    if not graph_data:
        return None

    # The model expects a batch, so we create a batch of size 1
    # The 'batch' tensor is needed for the global_mean_pool layer
    batch = torch.zeros(graph_data.num_nodes, dtype=torch.long)

    # Make the prediction
    with torch.no_grad(): # We don't need to calculate gradients for inference
        prediction = model(graph_data.x, graph_data.edge_index, batch)
    
    return prediction.item()