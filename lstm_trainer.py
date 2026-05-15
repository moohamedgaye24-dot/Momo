import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

class PriceLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_layer_size=50, output_size=1, num_layers=2):
        super(PriceLSTM, self).__init__()
        self.hidden_layer_size = hidden_layer_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_layer_size, num_layers, batch_first=True)
        self.linear = nn.Linear(hidden_layer_size, output_size)

    def forward(self, input_seq):
        lstm_out, _ = self.lstm(input_seq)
        predictions = self.linear(lstm_out[:, -1, :])
        return predictions

class LSTMTrainer:
    def __init__(self, symbol='GC=F', lookback_days=1825):
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.model_path = f"models/{self.symbol}_lstm.pth"
        if not os.path.exists("models"): os.makedirs("models")

    def fetch_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        df = yf.download(self.symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        if df.empty: raise ValueError("No data fetched.")
        return df['Close'].values.astype(np.float32)

    def prepare_data(self, data, seq_length=20):
        if isinstance(data, pd.Series): data = data.values
        data = data.astype(np.float32).flatten()
        self.data_min = np.min(data)
        self.data_max = np.max(data)
        normalized_data = (data - self.data_min) / (self.data_max - self.data_min)
        X, y = [], []
        for i in range(len(normalized_data) - seq_length):
            X.append(normalized_data[i:(i + seq_length)])
            y.append(normalized_data[i + seq_length])
        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.float32)
        return torch.tensor(X_arr).unsqueeze(-1), torch.tensor(y_arr).unsqueeze(-1)

    def train(self, epochs=2, batch_size=32):
        data = self.fetch_data()
        X, y = self.prepare_data(data)
        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        model = PriceLSTM()
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        model.train()
        for epoch in range(epochs):
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                y_pred = model(batch_X)
                loss = criterion(y_pred, batch_y)
                loss.backward()
                optimizer.step()
        torch.save({'model_state_dict': model.state_dict(), 'data_min': self.data_min, 'data_max': self.data_max}, self.model_path)

if __name__ == "__main__":
    LSTMTrainer().train()
