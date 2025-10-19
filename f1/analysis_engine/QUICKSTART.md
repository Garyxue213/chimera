# 🚀 Quick Start Guide

Get the F1 Analysis Engine running in 5 minutes.

## Step 1: Install Dependencies (1 minute)

```bash
cd /Users/gary/f1/analysis_engine
pip install -r requirements.txt
```

## Step 2: (Optional) Set Gemini API Key

For AI-powered insights:

```bash
# Get API key from: https://makersuite.google.com/app/apikey
export GEMINI_API_KEY='your-key-here'
```

**Note:** You can skip this - the system works without it!

## Step 3: Run the Analysis (3-5 minutes)

```bash
# Fetch real F1 data and generate reports
python main.py --all
```

This will:
1. Fetch Austin 2024 Qualifying, Sprint Q, and Sprint data
2. Process telemetry for all 20 drivers
3. Generate detailed lap-by-lap reports
4. Create comparisons

## Step 4: View Results

Reports are in `./reports/` directory:

```bash
# View available reports
ls -lh reports/

# Open a driver's report (Markdown format)
cat reports/VER_Qualifying_laps.md

# Or view with a text editor
open reports/LEC_Sprint_Qualifying_laps.md
```

## What You'll Get

### Per Driver, Per Session:
- `VER_Qualifying_laps.json` - Complete telemetry data
- `VER_Qualifying_laps.md` - Readable report

### Session Comparison:
- `Qualifying_comparison.json` - All drivers ranked
- Rankings, statistics, insights

## Example Report

Opening a markdown file shows:

```
# F1 Lap Analysis Report - VER (Qualifying)

## Lap 5 - 0:01:32.807

**Time:** 92.807s (Best)

**Performance:** 🟢 Best lap - Excellent

**Sectors:**
- S1: 30.123s
- S2: 31.456s
- S3: 31.228s

**Telemetry:**
- Max Speed: 314.5 km/h
- DRS: 2 activations
- Brakes: 8 events

**Issues:**
- Tire Degradation (3 laps old) → ~0.2s lost

**Highlights:**
- Strong Sector 1 - Excellent entry speed
```

## Commands Quick Reference

```bash
# Just fetch data
python main.py --fetch

# Just generate reports
python main.py --analyze ./f1_cache/austin_2024_complete.json

# Do everything
python main.py --all

# Different circuit/year
python main.py --all --year 2025 --circuit "Monaco"

# Check environment
python main.py --setup-check

# Help
python main.py --help
```

## File Structure

```
analysis_engine/
├── main.py                 # Main orchestrator
├── fastf1_fetcher.py      # Fetch real F1 data
├── report_generator.py    # Generate reports
├── gemini_analyzer.py     # AI analysis (optional)
├── requirements.txt       # Dependencies
├── f1_cache/              # Downloaded data (auto-created)
└── reports/               # Generated reports (auto-created)
```

## What Each File Does

| File | Purpose |
|------|---------|
| `fastf1_fetcher.py` | Fetches real telemetry from FastF1 |
| `report_generator.py` | Analyzes telemetry, identifies issues |
| `gemini_analyzer.py` | Uses AI for deeper insights (optional) |
| `main.py` | Orchestrates everything |

## Typical Output

```
🏁 F1 Analysis Engine - Setup Check
✅ Environment check complete

🚀 Fetching F1 Data
============================================================
Fetching Qualifying for Austin 2024...
✅ Loaded Qualifying session

Processing 20 drivers...
  [1/20] Processing ALB...  ✅ (10 laps)
  [2/20] Processing ALO...  ✅ (7 laps)
  ...
  [20/20] Processing VER... ✅ (14 laps)

✅ Data saved to ./f1_cache/austin_2024_complete.json

📄 Generating Analysis Reports
============================================================
📊 Generating reports for Qualifying...
  ✅ Qualifying_comparison.json
  ✅ ALB_Qualifying_laps.json + ALB_Qualifying_laps.md
  ✅ ALO_Qualifying_laps.json + ALO_Qualifying_laps.md
  ...

✅ All reports saved to ./reports

🎉 Analysis Complete!
```

## Troubleshooting

### "Module not found: fastf1"

```bash
# Install dependencies
pip install -r requirements.txt
```

### "Connection error"

```bash
# Try again - FastF1 caches data locally
# If problem persists, clear cache:
rm -rf f1_cache/
python main.py --fetch
```

### "GEMINI_API_KEY not set"

This is OK! You'll still get full telemetry analysis.
To get AI insights, set the key:

```bash
export GEMINI_API_KEY='your-key'
```

### "Data not available"

FastF1 data is available 30-120 minutes after each session ends.
Check if the session was recently completed.

## Next Steps

1. ✅ Run `python main.py --all`
2. ✅ Review reports in `./reports/`
3. ✅ Check markdown files for readable format
4. ✅ View JSON files for data to integrate
5. ✅ Integrate into React dashboard (see below)

## Integrate into React Dashboard

Copy reports to React dashboard:

```bash
# Copy reports to dashboard data folder
cp reports/* /Users/gary/f1/react-dashboard/public/data/reports/
```

Then in your React component:

```javascript
// Load driver report
fetch('/data/reports/VER_Qualifying_laps.json')
  .then(res => res.json())
  .then(data => {
    // Display lap-by-lap analysis
    data.lap_analysis.forEach(lap => {
      console.log(`${lap.timestamp}: ${lap.analysis.performance_assessment}`);
      lap.analysis.issues.forEach(issue => {
        console.log(`  ⚠️  ${issue.category}: ${issue.estimated_time_loss}`);
      });
    });
  });
```

## Support

For issues or questions:
- Check `README.md` for detailed documentation
- Review example reports in `./reports/`
- Check FastF1 docs: https://github.com/theOehrly/Fast-F1

---

**Ready?** Run this:

```bash
cd /Users/gary/f1/analysis_engine
pip install -r requirements.txt
python main.py --all
```

See you in 5 minutes! 🏁
