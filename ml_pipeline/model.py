import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool

class GNN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GNN, self).__init__()
        # Graph Convolutional Network layers
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)

        # A linear layer for the final prediction
        self.lin = torch.nn.Linear(hidden_channels, out_channels)

    def forward(self, x, edge_index, batch):
        # 1. First GCN layer + activation function
        x = self.conv1(x, edge_index)
        x = F.relu(x)

        # 2. Second GCN layer + activation function
        x = self.conv2(x, edge_index)
        x = F.relu(x)

        # 3. Readout layer: aggregate node features to get a graph-level feature
        x = global_mean_pool(x, batch)

        # 4. Final linear layer for prediction
        x = self.lin(x)

        return x

# --- TESTING BLOCK ---
if __name__ == '__main__':
    # Example of how to create the model
    # Input features will be 387 (384 from embedding + 2 for platform + 1 for node type)
    # We want to predict 1 output value (the virality score)
    model = GNN(in_channels=387, hidden_channels=64, out_channels=1)
    print("GNN Model Architecture:")
    print(model)