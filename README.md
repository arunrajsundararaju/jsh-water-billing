# Water Billing Calculator

Calculates per-unit water charges from meter readings and generates a Mygate-compatible CSV.

## How to use

### 1. Add meter reading files

Commit the previous and current month's Excel files to the `readings/` folder:

```
readings/JS-Jan-2026-Water-Meter-Readings.xlsx
readings/JS-Feb-2026-Water-Meter-Readings.xlsx
```

### 2. Run the workflow

- Go to **Actions** → **Water Billing** → **Run workflow**
- Fill in:
  - **Previous month filename**: e.g. `JS-Jan-2026-Water-Meter-Readings.xlsx`
  - **Current month filename**: e.g. `JS-Feb-2026-Water-Meter-Readings.xlsx`
  - **Total charges**: e.g. `20000`
  - **Output filename** (optional): e.g. `April_Meter_Based_Item_Upload.csv` (defaults to `Meter_Based_Item_Upload.csv`)
- Click **Run workflow**

### 3. Download the output

Once the workflow completes, click on the run and download the `Meter_Based_Item_Upload` artifact. This contains the CSV to upload to Mygate.

The workflow logs will also show the rate to manually enter in Mygate.

## Running locally

```
pip install pandas openpyxl
python water_billing.py prev.xlsx curr.xlsx 20000
```

## Notes

- Common meters (A-Common-1, A-Common-2, B-Common-1) are excluded from billing
- B-103 and B-104 are merged into a single B-103/104 unit
- The rate is rounded up to 4 decimal places (Mygate limitation), resulting in a small overshoot