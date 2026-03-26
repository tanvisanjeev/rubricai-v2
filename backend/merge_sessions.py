"""
merge_sessions.py

Pipeline that:
  1. Adds a 'completed' filter variable to each of the four session CSVs
     based on transcript markers
  2. Renames all columns with _user or _client suffix (except Participant ID)
  3. Merges all four files into a single CSV using Participant ID
  4. Adds a 'simulation' column indicating 'midday_market' or 'sunrise_cafe'

Input files (all in the same folder as this script):
    1-user-interview-midday-market-sessions.csv
    2-client-conversation-midday-market-sessions.csv
    1-user-interview-sunrise-cafe-sessions.csv
    2-client-conversation-sunrise-cafe-sessions.csv

Output:
    merged_sessions.csv

Usage:
    python merge_sessions.py
    python merge_sessions.py --input-dir /path/to/csvs --output merged.csv
"""

import argparse
import csv
import os
import sys
from collections import defaultdict, Counter

# ── Excluded emails ────────────────────────────────────────────────────────────
EXCLUDED_EMAILS = {
    "farah@cambiareducation.org",
    "cunger.neu@gmail.com",
    "sshane@collegiateacademies.org",
    "ian@schooljoy.com",
    "hyukhson@gmail.com",
    "taryn@cambiareducation.org",
    "a.ruda@northeastern.edu",
    "marie@cambiareducation.org",
    "test@gmail.com",
}

# ── Markers ────────────────────────────────────────────────────────────────────
USER_MARKER_A   = "You're about to begin the customer interview"
USER_MARKER_B   = "Thank you so much for doing this simulation"
CLIENT_MARKER_A = "I'm now going to switch roles and play the owner of"
CLIENT_MARKER_B = "Thank you so much for participating in this simulation"

# ── File config ────────────────────────────────────────────────────────────────
FILES = [
    {
        "filename":   "1-user-interview-midday-market-sessions.csv",
        "simulation": "midday_market",
        "suffix":     "_user",
        "marker_a":   USER_MARKER_A,
        "marker_b":   USER_MARKER_B,
    },
    {
        "filename":   "2-client-conversation-midday-market-sessions.csv",
        "simulation": "midday_market",
        "suffix":     "_client",
        "marker_a":   CLIENT_MARKER_A,
        "marker_b":   CLIENT_MARKER_B,
    },
    {
        "filename":   "1-user-interview-sunrise-cafe-sessions.csv",
        "simulation": "sunrise_cafe",
        "suffix":     "_user",
        "marker_a":   USER_MARKER_A,
        "marker_b":   USER_MARKER_B,
    },
    {
        "filename":   "2-client-conversation-sunrise-cafe-sessions.csv",
        "simulation": "sunrise_cafe",
        "suffix":     "_client",
        "marker_a":   CLIENT_MARKER_A,
        "marker_b":   CLIENT_MARKER_B,
    },
]


def normalize_col(name):
    """Lowercase and replace spaces with underscores: 'Participant ID' -> 'participant_id'"""
    return name.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")


def classify(text, marker_a, marker_b):
    has_a = marker_a.lower() in text.lower()
    has_b = marker_b.lower() in text.lower()
    if has_a and has_b:
        return "Complete"
    elif has_a:
        return "Partial"
    else:
        return "Incomplete"


def load_and_prepare(filepath, suffix, marker_a, marker_b, simulation):
    """
    Load a CSV, add 'completed', rename all columns with suffix
    (except Participant ID), add 'simulation' column.
    Returns list of dicts.
    """
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            sys.exit(f"Error: {filepath} appears to be empty.")
        if "Transcript" not in reader.fieldnames:
            sys.exit(f"Error: 'Transcript' column not found in {filepath}.")
        rows = list(reader)

    # Filter out excluded emails (case-insensitive)
    before = len(rows)
    if "Email" in rows[0]:
        rows = [r for r in rows if r.get("Email", "").strip().lower() not in {e.lower() for e in EXCLUDED_EMAILS}]
        removed = before - len(rows)
        if removed:
            print(f"  Removed {removed} row(s) matching excluded emails.")

    prepared = []
    for row in rows:
        new_row = {"participant_id": row["Participant ID"], "simulation": simulation}
        # Add completed based on transcript
        new_row[f"completed{suffix}"] = classify(row["Transcript"], marker_a, marker_b)
        # Rename all other columns: lowercase + underscores + suffix
        for col in row:
            if col != "Participant ID":
                new_row[f"{normalize_col(col)}{suffix}"] = row[col]
        prepared.append(new_row)

    return prepared


def merge(all_data):
    """
    Merge four lists of dicts on participant_id + simulation.
    Each participant+simulation combo gets one row with _user and _client columns.
    """
    grouped = defaultdict(dict)
    for row in all_data:
        key = (row["participant_id"], row["simulation"])
        grouped[key].update(row)

    return [{"participant_id": k[0], "simulation": k[1], **v}
            for k, v in grouped.items()]


def get_fieldnames(merged_rows):
    """Build ordered fieldnames: participant_id, simulation, then _user cols, then _client cols."""
    user_cols   = sorted({k for row in merged_rows for k in row if k.endswith("_user")})
    client_cols = sorted({k for row in merged_rows for k in row if k.endswith("_client")})
    return ["participant_id", "simulation"] + user_cols + client_cols


def main():
    parser = argparse.ArgumentParser(
        description="Add completion filter, rename columns, and merge all four session CSVs."
    )
    parser.add_argument(
        "--input-dir",
        default=".",
        help="Folder containing the four input CSVs (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default="merged_sessions.csv",
        help="Output file path (default: merged_sessions.csv)"
    )
    args = parser.parse_args()

    all_data = []
    for config in FILES:
        filepath = os.path.join(args.input_dir, config["filename"])
        if not os.path.isfile(filepath):
            sys.exit(f"Error: file not found — {filepath}")
        print(f"Loading {config['filename']}...")
        rows = load_and_prepare(
            filepath,
            suffix     = config["suffix"],
            marker_a   = config["marker_a"],
            marker_b   = config["marker_b"],
            simulation = config["simulation"],
        )
        all_data.extend(rows)
        # Print per-file completion summary
        counts = Counter(r[f"completed{config['suffix']}"] for r in rows)
        print(f"  Complete: {counts['Complete']}  Partial: {counts['Partial']}  Incomplete: {counts['Incomplete']}")

    print("\nMerging...")
    merged = merge(all_data)
    fieldnames = get_fieldnames(merged)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)

    print(f"\nDone! {len(merged)} rows written to {args.output}")
    print(f"Columns: {', '.join(fieldnames)}")


if __name__ == "__main__":
    main()
