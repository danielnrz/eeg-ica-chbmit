from __future__ import annotations

import os
import matplotlib.pyplot as plt
import mne
from mne.preprocessing import ICA

from .channel_map import TARGET_CHANNELS, safe_rename_and_pick

def clean_one_edf(
    file_path: str,
    output_clean_dir: str,
    output_report_dir: str,
    notch_hz: float = 60.0,
    l_freq: float = 1.0,
    h_freq: float = 40.0,
    max_components: int = 15,
    random_state: int = 97,
    max_iter: int = 800,
):
    """Load a CHB-MIT EDF, standardize channels, filter, run ICA, auto-detect blinks, and save outputs.

    Returns:
        status (str): 'Success' or a short reason for skipping/failure.
    """
    base_name = os.path.basename(file_path).replace(".edf", "")

    # 1) Load
    try:
        raw = mne.io.read_raw_edf(file_path, preload=True, verbose=False)
        raw.set_meas_date(None)  # Fix MNE date warnings in some files
    except Exception as e:
        return f"Load Error: {e}"

    # 2) Rename + pick
    try:
        raw = safe_rename_and_pick(raw)
        available = [ch for ch in TARGET_CHANNELS if ch in raw.ch_names]
        if len(available) < 5:
            return "Skipped (Not enough channels)"
        raw.pick(available)
    except Exception as e:
        return f"Rename Error: {e}"

    # 3) Channel types & montage
    raw.set_channel_types({ch: "eeg" for ch in raw.ch_names})
    montage = mne.channels.make_standard_montage("standard_1020")
    try:
        raw.set_montage(montage, on_missing="ignore")
    except Exception:
        pass

    # 4) Filtering
    raw.notch_filter(freqs=[notch_hz], trans_bandwidth=3, verbose=False)
    raw.filter(l_freq=l_freq, h_freq=h_freq, verbose=False)

    # 5) ICA
    n_comps = min(max_components, len(raw.ch_names) - 1)
    if n_comps < 2:
        return "Skipped (Low Rank)"

    ica = ICA(n_components=n_comps, random_state=random_state, max_iter=max_iter)
    ica.fit(raw, verbose=False)

    # 6) Blink detection (heuristic): use Fp1 if available
    eog_indices = []
    if "Fp1" in raw.ch_names:
        try:
            eog_indices, _ = ica.find_bads_eog(raw, ch_name="Fp1", verbose=False)
            ica.exclude = eog_indices
        except Exception:
            pass

    # 7) Save ICA component report image
    os.makedirs(output_report_dir, exist_ok=True)
    title_str = f"File: {base_name} | Blinks: {eog_indices}" if eog_indices else f"File: {base_name}"
    try:
        fig = ica.plot_components(show=False, title=title_str)
        fig.savefig(os.path.join(output_report_dir, f"{base_name}_ica.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)
    except Exception:
        pass

    # 8) Apply ICA and save cleaned FIF
    os.makedirs(output_clean_dir, exist_ok=True)
    raw_clean = raw.copy()
    ica.apply(raw_clean, verbose=False)
    raw_clean.save(os.path.join(output_clean_dir, f"clean_{base_name}_eeg.fif"), overwrite=True, verbose=False)

    return "Success"
