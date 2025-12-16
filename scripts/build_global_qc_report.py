from __future__ import annotations

import argparse
import glob
import os
import pandas as pd
from tqdm import tqdm
import mne
import numpy as np

from eeg_ica.qc_metrics import variance_reduction_proxy

def calculate_file_metrics(raw_path: str, clean_path: str):
    try:
        raw = mne.io.read_raw_edf(raw_path, preload=True, verbose=False)
        clean = mne.io.read_raw_fif(clean_path, preload=True, verbose=False)

        target_raw = "FP1-F7" if "FP1-F7" in raw.ch_names else raw.ch_names[0]
        target_clean = "Fp1" if "Fp1" in clean.ch_names else clean.ch_names[0]

        d_raw = raw.get_data(picks=[target_raw])[0]
        d_clean = clean.get_data(picks=[target_clean])[0]

        red = variance_reduction_proxy(d_raw, d_clean)

        var_raw = float(np.var(d_raw))
        var_clean = float(np.var(d_clean))

        # If something goes very wrong numerically, clip extreme negatives
        if red < -100:
            red = -100.0

        return red, var_raw, var_clean
    except Exception:
        return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Build a global QC report (variance reduction proxy) for cleaned CHB-MIT files.")
    parser.add_argument("--dataset_root", type=str, default="Dataset/CHB-MIT", help="Path to CHB-MIT root.")
    parser.add_argument("--cleaned_root", type=str, default="ProcessedDataset/Cleaned_Data", help="Root containing per-patient cleaned FIF folders.")
    parser.add_argument("--out_csv", type=str, default="ProcessedDataset/Global_Quality_Report.csv", help="Where to save the CSV report.")
    args = parser.parse_args()

    mne.set_log_level("WARNING")

    results = []
    patient_ids = [f"chb{i:02d}" for i in range(1, 25)]

    print("Starting Global Quality Control Analysis...")
    for pid in tqdm(patient_ids):
        clean_folder = os.path.join(args.cleaned_root, pid)
        if not os.path.exists(clean_folder):
            continue

        clean_files = glob.glob(os.path.join(clean_folder, "*.fif"))
        for c_file in clean_files:
            base_name = os.path.basename(c_file).replace("clean_", "").replace("_eeg.fif", ".edf")
            raw_file = os.path.join(args.dataset_root, pid, base_name)

            if os.path.exists(raw_file):
                red, v_raw, v_clean = calculate_file_metrics(raw_file, c_file)
                if red is None:
                    continue
                results.append({
                    "Patient": pid,
                    "File": base_name,
                    "Variance_Reduction_Percent": red,
                    "Raw_Variance": v_raw,
                    "Clean_Variance": v_clean,
                })

    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    df.to_csv(args.out_csv, index=False)
    print(f"Saved QC report to: {args.out_csv} (rows={len(df)})")

if __name__ == "__main__":
    main()
