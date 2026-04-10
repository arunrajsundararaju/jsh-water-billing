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

if __name__ == "__main__":
    main()