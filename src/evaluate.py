"""Compare Claude's answers with manually evaluated labels.
"""
from pathlib import Path

import pandas as pd

from claude_client import send_ticket

EVAL_FILE = Path("data/eval_set.csv")
FIELDS = ["category", "priority", "effort"]

labels = pd.read_csv(EVAL_FILE, sep=None, engine="python", encoding="utf-8-sig", dtype=str)

# Only use rows with all three labels.
labels = labels.dropna(subset=FIELDS)
for field in FIELDS:
    labels[field] = labels[field].str.strip().str.lower()
print(f"Evaluating {len(labels)} labelled tickets...")

rows = []
for _, ticket in labels.iterrows():
    answer = send_ticket(ticket["message"])
    row = {"ticket_id": ticket["ticket_id"], "message": ticket["message"]}
    for field in FIELDS:
        row[f"{field}_label"] = ticket[field]
        row[f"{field}_claude"] = getattr(answer, field)
    rows.append(row)
    print(f"  {ticket['ticket_id']} done")

results = pd.DataFrame(rows)

print("\nScore per field (Claude matches your label):")
for field in FIELDS:
    correct = (results[f"{field}_label"] == results[f"{field}_claude"]).sum()
    print(f"  {field:<9} {correct}/{len(results)}  ({correct / len(results):.0%})")

print("\nDisagreements:")
for field in FIELDS:
    wrong = results[results[f"{field}_label"] != results[f"{field}_claude"]]
    for _, r in wrong.iterrows():
        print(f"  [{field}] {r['ticket_id']}: you={r[f'{field}_label']}, claude={r[f'{field}_claude']}")
        print(f"      {r['message'][:120]}")
