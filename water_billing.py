import sys
import math
import pandas as pd

USAGE = """
Water Billing Calculator
========================
Usage:
    python water_billing.py <previous_month.xlsx> <current_month.xlsx> <total_tanker_charges_rupees> [output.csv]

Example:
    python water_billing.py JS-Jan-2026-Water-Meter-Readings.xlsx JS-Feb-2026-Water-Meter-Readings.xlsx 20000
"""

COMMON_METERS = {"A-Common-1", "A-Common-2", "B-Common-1"}

# Meters that should be combined into a single Mygate unit
COMBINED_UNITS = {
    "B-103/104": ["B-103", "B-104"],
}

# Reverse lookup: meter name -> combined Mygate name
# e.g. {"B-103": "B-103/104", "B-104": "B-103/104"}
METER_TO_COMBINED = {}
for mygate_name, meters in COMBINED_UNITS.items():
    for m in meters:
        METER_TO_COMBINED[m] = mygate_name

def read_meter_file(path):
    """Read a meter readings xlsx and return {unit_name: reading} dict."""
    df = pd.read_excel(path, header=None, skiprows=1, names=["Unit Name", "Current Reading"])
    df["Unit Name"] = df["Unit Name"].astype(str).str.strip()
    df["Current Reading"] = pd.to_numeric(df["Current Reading"], errors="coerce")
    return dict(zip(df["Unit Name"], df["Current Reading"]))

def main():
    if len(sys.argv) < 4:
        print(USAGE)
        sys.exit(1)

    prev_file = sys.argv[1]
    curr_file = sys.argv[2]
    total_charges = float(sys.argv[3])
    output_csv = sys.argv[4] if len(sys.argv) > 4 else "Meter_Based_Item_Upload.csv"

    print(f"Previous file  : {prev_file}")
    print(f"Current file   : {curr_file}")
    print(f"Total charges  : Rs. {total_charges:,.2f}")
    print(f"Output CSV     : {output_csv}")
    print()

    prev_readings = read_meter_file(prev_file)
    curr_readings = read_meter_file(curr_file)
 
    print(f"Loaded {len(prev_readings)} meters from: {prev_file}")
    print(f"Loaded {len(curr_readings)} meters from: {curr_file}")
    print()

    print("Sample readings (first 5):")
    for i, (unit, reading) in enumerate(prev_readings.items()):
        if i >= 5:
            break
        curr = curr_readings.get(unit, "N/A")
        print(f"  {unit:<15} Prev: {reading:>10,.0f}   Curr: {curr:>10,.0f}")
    print()

    # Filter out common meters, keep only individual apartments
    all_units = sorted(set(prev_readings.keys()) | set(curr_readings.keys()))

    # Loop through all_units and build a new list keeping only
    # the units that are NOT in COMMON_METERS.
    # Equivalent to:
    #   individual_units = []
    #   for u in all_units:
    #       if u not in COMMON_METERS:
    #           individual_units.append(u)
    individual_units = [u for u in all_units if u not in COMMON_METERS]

    print(f"Total meters: {len(all_units)}")
    print(f"Common meters excluded: {len(all_units) - len(individual_units)}")
    print(f"Individual apartments: {len(individual_units)}")
    print()

    # Show common meter consumption for reference
    print("COMMON METERS (excluded from billing):")
    for unit in sorted(COMMON_METERS):
        p = int(prev_readings.get(unit, 0))
        c = int(curr_readings.get(unit, 0))
        print(f"  {unit:<15} {p:>8,} -> {c:>8,} = {c - p:>6,} units")

    # Calculate consumption for each individual apartment
    records = []
    for unit in individual_units:
        prev = prev_readings.get(unit)
        curr = curr_readings.get(unit)
        if prev is None or curr is None or pd.isna(prev) or pd.isna(curr):
            print(f"  WARNING: Missing reading for {unit}, skipping.")
            continue
        consumption = int(curr - prev)
        if consumption < 0:
            print(f"  WARNING: Negative consumption for {unit} ({prev} -> {curr}), treating as 0.")
            consumption = 0
        records.append((unit, int(prev), int(curr), consumption))
 
    # Calculate rate
    total_consumption = sum(r[3] for r in records)
    if total_consumption == 0:
        print("ERROR: Total consumption is zero. Cannot calculate rate.")
        sys.exit(1)

    exact_rate = total_charges / total_consumption
    # Mygate only accepts 4 decimal places, so round UP to avoid under-collection
    mygate_rate = math.ceil(exact_rate * 10000) / 10000
    mygate_total = mygate_rate * total_consumption
    overshoot = mygate_total - total_charges

    # Print summary
    print("=" * 65)
    print(f"  Total charges    : Rs. {total_charges:,.2f}")
    print(f"  Total consumption: {total_consumption:,} units")
    print(f"  Apartments       : {len(records)}")
    print(f"  Exact rate       : Rs. {exact_rate:.10f}")
    print(f"  Mygate rate (4dp): Rs. {mygate_rate:.4f}")
    print(f"  Mygate total     : Rs. {mygate_total:,.2f}")
    print(f"  Overshoot        : Rs. {overshoot:,.2f}")
    print("=" * 65)
 
    # Print apartment breakdown using Mygate rate
    print(f"\n  {'Unit':<12} {'Prev':>10} {'Curr':>10} {'Units':>8} {'Amount':>12}")
    print("  " + "-" * 54)
    total_amount = 0
    for unit, prev, curr, consumption in records:
        amount = consumption * mygate_rate
        total_amount += amount
        print(f"  {unit:<12} {prev:>10,} {curr:>10,} {consumption:>8,} {amount:>12,.2f}")
    print("  " + "-" * 54)
    print(f"  {'TOTAL':<12} {'':>10} {'':>10} {total_consumption:>8,} {total_amount:>12,.2f}")
 
    print(f"\n>>> RATE FOR MYGATE: Rs. {mygate_rate:.4f} per unit <<<")

    # ---------------------------------------------------------------
    # Merge B-103 and B-104 into B-103/104 for Mygate CSV
    # ---------------------------------------------------------------
    # Split records into two buckets: regular apartments and combined meters
    merged = []
    combined_pending = {}  # {"B-103/104": [(unit, prev, curr, cons), ...]}

    for unit, prev, curr, consumption in records:
        if unit in METER_TO_COMBINED:
            # This meter belongs to a combined unit, collect it
            mygate_name = METER_TO_COMBINED[unit]
            combined_pending.setdefault(mygate_name, []).append((unit, prev, curr, consumption))
        else:
            # Regular apartment, keep as-is
            # "parts" stores the individual meter details (just one here)
            merged.append({
                "unit": unit,
                "consumption": consumption,
                "parts": [(unit, prev, curr, consumption)],
            })

    # Now combine the collected meters into single entries
    for mygate_name, parts in combined_pending.items():
        merged.append({
            "unit": mygate_name,
            "consumption": sum(p[3] for p in parts),
            "parts": parts,  # keep individual meter details for the narration
        })

    # ---------------------------------------------------------------
    # Generate Mygate CSV
    # ---------------------------------------------------------------
    csv_rows = []
    for r in sorted(merged, key=lambda x: x["unit"]):
        if len(r["parts"]) == 1:
            # Regular apartment - single meter
            _, prev, curr, cons = r["parts"][0]
            csv_prev = prev
            csv_curr = curr
            desc = (
                f"Rate: Rs.{mygate_rate:.4f}/unit | "
                f"Prev: {prev:,} | Curr: {curr:,} | "
                f"Consumption: {cons:,} units"
            )
        else:
            # Combined unit (B-103/104) - sum prev and curr for CSV fields
            csv_prev = sum(p[1] for p in r["parts"])
            csv_curr = sum(p[2] for p in r["parts"])
            part_details = [f"{name}: {p}->{c}={cons}" for name, p, c, cons in r["parts"]]
            desc = (
                f"Rate: Rs.{mygate_rate:.4f}/unit | "
                f"Total consumption: {r['consumption']:,} units | "
                + " | ".join(part_details)
            )

        csv_rows.append({
            "Unit Name": r["unit"],
            "Previous Reading": csv_prev,
            "Current Reading": csv_curr,
            "Discount Amount (if applicable)": "",
            "Additional Description (optional)": desc,
            "Discount Description (optional)": "",
        })

    df_out = pd.DataFrame(csv_rows)
    df_out.to_csv(output_csv, index=False)
    print(f"\nMygate CSV written to: {output_csv}")

if __name__ == "__main__":
    main()