from __future__ import annotations

import argparse
import numpy as np
import matplotlib.pyplot as plt
import mne
from scipy.stats import kurtosis

def main():
    parser = argparse.ArgumentParser(description="QC visualization for one raw/clean pair (time series + PSD).")
    parser.add_argument("--raw", type=str, required=True, help="Path to raw EDF file.")
    parser.add_argument("--clean", type=str, required=True, help="Path to cleaned FIF file.")
    parser.add_argument("--duration", type=float, default=10.0, help="Seconds to visualize from t=0.")
    parser.add_argument("--fmax", type=float, default=80.0, help="Max frequency for PSD.")
    args = parser.parse_args()

    mne.set_log_level("WARNING")

    raw = mne.io.read_raw_edf(args.raw, preload=True, verbose=False)
    clean = mne.io.read_raw_fif(args.clean, preload=True, verbose=False)

    target_raw = "FP1-F7" if "FP1-F7" in raw.ch_names else raw.ch_names[0]
    target_clean = "Fp1" if "Fp1" in clean.ch_names else clean.ch_names[0]

    d_raw = raw.get_data(picks=[target_raw])[0] * 1e6  # microvolts
    d_clean = clean.get_data(picks=[target_clean])[0] * 1e6
    times = raw.times

    var_raw = float(np.var(d_raw))
    var_clean = float(np.var(d_clean))
    var_reduction = (1 - var_clean / var_raw) * 100 if var_raw != 0 else 0.0

    k_raw = float(kurtosis(d_raw))
    k_clean = float(kurtosis(d_clean))

    noise = d_raw - d_clean
    power_signal = float(np.mean(d_clean ** 2))
    power_noise = float(np.mean(noise ** 2))
    snr = 10 * np.log10(power_signal / power_noise) if power_noise != 0 else float("inf")

    print("QC REPORT")
    print("-" * 40)
    print(f"Raw channel:   {target_raw}")
    print(f"Clean channel: {target_clean}")
    print(f"Variance reduction: {var_reduction:.2f}%")
    print(f"Kurtosis: {k_raw:.2f} -> {k_clean:.2f}")
    print(f"Estimated SNR: {snr:.2f} dB")
    print("-" * 40)

    # Plot
    plt.figure(figsize=(14, 10))

    # Time domain
    plt.subplot(2, 1, 1)
    idx_e = int(args.duration * raw.info["sfreq"])
    plt.plot(times[:idx_e], d_raw[:idx_e], alpha=0.4, label="Raw (Noisy)")
    plt.plot(times[:idx_e], d_clean[:idx_e], linewidth=1.5, label="Cleaned (ICA)")
    plt.title(f"Artifact Removal Visualization (Var Red: {var_reduction:.1f}%, Kurtosis: {k_raw:.1f} → {k_clean:.1f})")
    plt.ylabel("Amplitude (µV)")
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)

    # PSD
    plt.subplot(2, 1, 2)
    psd_r, f_r = mne.time_frequency.psd_array_welch(d_raw, raw.info["sfreq"], fmax=args.fmax, verbose=False)
    psd_c, f_c = mne.time_frequency.psd_array_welch(d_clean, raw.info["sfreq"], fmax=args.fmax, verbose=False)
    plt.plot(f_r, 10 * np.log10(psd_r), alpha=0.5, label="Raw Spectrum")
    plt.plot(f_c, 10 * np.log10(psd_c), label="Cleaned Spectrum")
    plt.axvline(60, linestyle="--", alpha=0.6, label="60Hz Mains")
    plt.axvline(40, linestyle=":", alpha=0.6, label="40Hz Cutoff")
    plt.title("Power Spectral Density (filtering & artifact power loss)")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power (dB)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
