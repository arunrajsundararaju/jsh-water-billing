import sys
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
    rate = total_charges / total_consumption
 
    # Print summary
    print("=" * 65)
    print(f"  Total charges    : Rs. {total_charges:,.2f}")
    print(f"  Total consumption: {total_consumption:,} units")
    print(f"  Apartments       : {len(records)}")
    print(f"  Rate per unit    : Rs. {rate:.4f}")
    print("=" * 65)
 
    # Print apartment breakdown
    print(f"\n  {'Unit':<12} {'Prev':>10} {'Curr':>10} {'Units':>8} {'Amount':>12}")
    print("  " + "-" * 54)
    total_amount = 0
    for unit, prev, curr, consumption in records:
        amount = consumption * rate
        total_amount += amount
        print(f"  {unit:<12} {prev:>10,} {curr:>10,} {consumption:>8,} {amount:>12,.2f}")
    print("  " + "-" * 54)
    print(f"  {'TOTAL':<12} {'':>10} {'':>10} {total_consumption:>8,} {total_amount:>12,.2f}")
 
    print(f"\n>>> RATE FOR MYGATE: Rs. {rate:.4f} per unit <<<")

if __name__ == "__main__":
    main()