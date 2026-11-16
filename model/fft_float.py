"""
fft_float.py - Floating-point reference model and spectral error metrics.
Supports arbitrary power-of-2 Radix-2 DIT FFT with configurable stage scaling.
"""

import numpy as np


def fft_float_reference(x, scale_per_stage=True):
    """
    Computes double-precision complex FFT using Radix-2 DIT algorithm or NumPy FFT.
    
    Args:
        x: Input array (1D complex or real). Length must be a power of 2.
        scale_per_stage: If True, applies 1/2 scaling at each radix-2 stage (total 1/N scaling).
                         Matches the hardware stage-scaling implementation.
    Returns:
        X: Complex numpy array of length N.
    """
    x = np.asarray(x, dtype=np.complex128)
    N = len(x)
    assert (N & (N - 1)) == 0 and N > 0, "Length N must be a power of 2."
    
    X_unscaled = np.fft.fft(x)
    if scale_per_stage:
        return X_unscaled / N
    else:
        return X_unscaled


def calculate_snr(ref, test):
    """
    Computes Signal-to-Quantization-Noise Ratio (SQNR) in dB.
    SNR = 10 * log10( sum(|ref|^2) / sum(|ref - test|^2) )
    """
    ref = np.asarray(ref, dtype=np.complex128)
    test = np.asarray(test, dtype=np.complex128)
    
    signal_power = np.sum(np.abs(ref) ** 2)
    noise_power = np.sum(np.abs(ref - test) ** 2)
    
    if noise_power == 0:
        return float('inf')
    if signal_power == 0:
        return 0.0
    return 10.0 * np.log10(signal_power / noise_power)


def calculate_rmse(ref, test):
    """
    Computes Root Mean Square Error (RMSE).
    RMSE = sqrt( mean(|ref - test|^2) )
    """
    ref = np.asarray(ref, dtype=np.complex128)
    test = np.asarray(test, dtype=np.complex128)
    return float(np.sqrt(np.mean(np.abs(ref - test) ** 2)))


def calculate_max_error(ref, test):
    """
    Computes Maximum Absolute Error across all real and imaginary components.
    """
    ref = np.asarray(ref, dtype=np.complex128)
    test = np.asarray(test, dtype=np.complex128)
    err_real = np.max(np.abs(np.real(ref) - np.real(test)))
    err_imag = np.max(np.abs(np.imag(ref) - np.imag(test)))
    return float(max(err_real, err_imag))


if __name__ == "__main__":
    N = 64
    t = np.arange(N)
    # Test with complex tone
    x = np.exp(1j * 2 * np.pi * 5 * t / N) * 0.9
    X = fft_float_reference(x, scale_per_stage=True)
    print(f"Float reference test N={N} successful.")
    print(f"Max bin magnitude: {np.max(np.abs(X)):.4f} at bin {np.argmax(np.abs(X))}")
