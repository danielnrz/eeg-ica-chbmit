from __future__ import annotations

import argparse
import glob
import os
from tqdm import tqdm
import mne

from eeg_ica.ica_clean import clean_one_edf

def main():
    parser = argparse.ArgumentParser(description="Batch EEG cleaning (CHB-MIT) using MNE + ICA.")
    parser.add_argument("--dataset_root", type=str, default="Dataset/CHB-MIT", help="Path to CHB-MIT root (contains chb01..chb24).")
    parser.add_argument("--processed_root", type=str, default="ProcessedDataset", help="Output root folder.")
    args = parser.parse_args()

    mne.set_log_level("WARNING")

    patient_ids = [f"chb{i:02d}" for i in range(1, 25)]
    print(f"Starting batch processing for {len(patient_ids)} patients...")

    for pid in patient_ids:
        in_folder = os.path.join(args.dataset_root, pid)
        if not os.path.exists(in_folder):
            print(f"Dataset folder for {pid} not found. Skipping.")
            continue

        clean_out = os.path.join(args.processed_root, "Cleaned_Data", pid)
        report_out = os.path.join(args.processed_root, "ICA_Reports", pid)
        os.makedirs(clean_out, exist_ok=True)
        os.makedirs(report_out, exist_ok=True)

        edf_files = sorted(glob.glob(os.path.join(in_folder, "*.edf")))
        if not edf_files:
            print(f"No EDF files in {pid}. Skipping.")
            continue

        print(f"Processing {pid} ({len(edf_files)} files)...")
        for fpath in tqdm(edf_files, desc=f"{pid}", leave=False):
            status = clean_one_edf(fpath, clean_out, report_out)
            # For speed, keep logging minimal. Uncomment if debugging:
            # if status != "Success":
            #     print(f"[{pid}] {os.path.basename(fpath)} -> {status}")

    print("All patients processed.")

if __name__ == "__main__":
    main()
