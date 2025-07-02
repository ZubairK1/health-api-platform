import numpy as np

def apply_differential_privacy(value, sensitivity=1.0, epsilon=1.0):
    noise = np.random.laplace(0, sensitivity / epsilon)
    return value + noise
