import numpy as np

class SingularityEngine:
    def __init__(self): pass

    def compute_fft(self, prices):
        if len(prices) < 2: return 0.0, 1.0
        fft_result = np.fft.fft(prices)
        magnitudes = np.abs(fft_result)
        cutoff = len(magnitudes) // 2
        signal = np.sum(magnitudes[:cutoff])
        noise = np.sum(magnitudes[cutoff:])
        if signal == 0: return 0.0, 1.0
        return noise / signal, signal

    def compute_laurent_divergence(self, prices):
        if len(prices) < 5: return 0.0
        ma = np.mean(prices)
        current = prices[-1]
        return abs((current - ma) / ma)

    def analyze_market_dissonance(self, window_data):
        if 'Close' not in window_data.columns: return False, 0.0
        prices = window_data['Close'].values
        noise_ratio, _ = self.compute_fft(prices)
        divergence = self.compute_laurent_divergence(prices)
        is_dissonant = (noise_ratio > 0.4) or (divergence > 0.02)
        return is_dissonant, noise_ratio

    def execute_rao_swarm(self, window_data):
        return np.random.choice([True, False], p=[0.2, 0.8])
