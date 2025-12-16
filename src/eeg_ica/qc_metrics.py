from __future__ import annotations

import numpy as np
import mne
from scipy.stats import kurtosis

def variance_reduction_proxy(d_raw: np.ndarray, d_clean: np.ndarray) -> float:
    """Variance reduction proxy in percent: (1 - var(clean)/var(raw)) * 100."""
    var_raw = float(np.var(d_raw))
    var_clean = float(np.var(d_clean))
    if var_raw == 0:
        return 0.0
    return (1.0 - (var_clean / var_raw)) * 100.0

def estimated_snr_db(d_clean: np.ndarray, noise_signal: np.ndarray) -> float:
    """Estimated SNR in dB using power(clean) / power(noise)."""
    power_signal = float(np.mean(d_clean ** 2))
    power_noise = float(np.mean(noise_signal ** 2))
    if power_noise == 0:
        return float("inf")
    return 10.0 * np.log10(power_signal / power_noise)

def load_raw_and_clean(raw_path: str, clean_path: str):
    raw = mne.io.read_raw_edf(raw_path, preload=True, verbose=False)
    clean = mne.io.read_raw_fif(clean_path, preload=True, verbose=False)
    return raw, clean

def pick_front_channel(raw, clean):
    """Heuristic channel selection matching the notebook.

    NOTE: In CHB-MIT, raw channels can be bipolar (e.g., 'FP1-F7'), while cleaned channels
    are renamed to single labels (e.g., 'Fp1'). Treat comparisons as a proxy, not ground truth.
    """
    target_raw = "FP1-F7" if "FP1-F7" in raw.ch_names else raw.ch_names[0]
    target_clean = "Fp1" if "Fp1" in clean.ch_names else clean.ch_names[0]
    return target_raw, target_clean

def compute_single_file_metrics(raw_path: str, clean_path: str):
    raw, clean = load_raw_and_clean(raw_path, clean_path)
    tr, tc = pick_front_channel(raw, clean)

    d_raw = raw.get_data(picks=[tr])[0]
    d_clean = clean.get_data(picks=[tc])[0]

    red = variance_reduction_proxy(d_raw, d_clean)
    k_raw = float(kurtosis(d_raw))
    k_clean = float(kurtosis(d_clean))
    noise = d_raw - d_clean
    snr = estimated_snr_db(d_clean, noise)

    return {
        "target_raw": tr,
        "target_clean": tc,
        "variance_reduction_percent": red,
        "kurtosis_raw": k_raw,
        "kurtosis_clean": k_clean,
        "estimated_snr_db": snr,
    }
