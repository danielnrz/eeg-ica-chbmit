from __future__ import annotations

# Final channel list (10-20 system, as used in the notebook)
TARGET_CHANNELS = [
    "Fp1","F7","T7","P7","O1","F3","C3","P3",
    "Fp2","F4","C4","P4","O2","F8","T8","P8",
    "Fz","Cz","Pz"
]

# Mapping dictionary (handles CHB-MIT bipolar labels and a few duplicates)
MAPPING_DICT = {
    "FP1-F7": "Fp1", "F7-T7": "F7", "T7-P7": "T7", "P7-O1": "P7",
    "FP1-F3": "F3", "F3-C3": "C3", "C3-P3": "P3", "P3-O1": "O1",
    "FP2-F4": "Fp2", "F4-C4": "F4", "C4-P4": "C4", "P4-O2": "P4",
    "FP2-F8": "F8", "F8-T8": "T8", "T8-P8": "P8", "P8-O2": "O2",
    "FZ-CZ": "Fz", "CZ-PZ": "Cz", "PZ-OZ": "Pz",
    "T8-P8-0": "P8", "T8-P8-1": "P8", "T8-P8-2": "P8",
}

def safe_rename_and_pick(raw):
    """Prevent name collisions and remove duplicates based on MAPPING_DICT.

    CHB-MIT channel names sometimes include bipolar derivations and duplicates.
    This function maps known names to TARGET_CHANNELS and drops collisions.
    """
    current_names = raw.ch_names
    rename_map = {}
    used_targets = set()
    channels_to_drop = []

    for ch in current_names:
        clean_name_key = ch
        if ch not in MAPPING_DICT:
            # handle names like 'A-B-C' by truncating to 'A-B'
            if "-" in ch and len(ch.split("-")) > 2:
                clean_name_key = "-".join(ch.split("-")[:2])

        if ch in MAPPING_DICT:
            target = MAPPING_DICT[ch]
        elif clean_name_key in MAPPING_DICT:
            target = MAPPING_DICT[clean_name_key]
        else:
            continue

        if target in used_targets:
            channels_to_drop.append(ch)
        else:
            rename_map[ch] = target
            used_targets.add(target)

    if channels_to_drop:
        raw.drop_channels(channels_to_drop)
    raw.rename_channels(rename_map)
    return raw
