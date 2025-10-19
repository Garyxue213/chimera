# 🔗 F1 Analysis Integration Guide

Complete guide for integrating the F1 Analysis Engine with the React Dashboard.

## Overview

The Analysis Engine generates detailed lap-by-lap reports. The React Dashboard displays them in an interactive UI.

## Step 1: Generate Analysis Reports

First, generate the reports from the Analysis Engine:

```bash
cd /Users/gary/f1/analysis_engine
pip install -r requirements.txt
python main.py --all
```

This creates reports in:
```
/Users/gary/f1/analysis_engine/reports/
├── Qualifying_comparison.json
├── VER_Qualifying_laps.json
├── VER_Qualifying_laps.md
├── LEC_Qualifying_laps.json
├── LEC_Qualifying_laps.md
└── ... (all drivers and sessions)
```

## Step 2: Copy Reports to Dashboard

Copy the generated reports to the dashboard's public data folder:

```bash
# Create reports directory if it doesn't exist
mkdir -p /Users/gary/f1/react-dashboard/public/data/reports

# Copy all reports
cp /Users/gary/f1/analysis_engine/reports/* \
   /Users/gary/f1/react-dashboard/public/data/reports/
```

## Step 3: Start React Dashboard

```bash
cd /Users/gary/f1/react-dashboard
npm run dev
```

Opens at: `http://localhost:3001`

## Step 4: View Analysis Reports

1. **Select a Driver** - Click any driver in the sidebar
2. **Switch to "Analysis" Tab** - New ⏱️ Analysis tab
3. **Browse Laps** - Click lap numbers to see details
4. **View Issues** - See where time was lost
5. **Check Highlights** - See what went well

## Features in Dashboard

### Lap Timeline
```
[L1]  [L2]  [L3⭐] [L4]  [L5⚠️]
 9.5s  9.4s  9.2s  9.6s  9.3s
```
- Click any lap to see details
- ⭐ marks best lap
- ⚠️ shows issues count
- Color-coded by performance

### Lap Details

Shows:
- **Lap Time** - Overall performance
- **Sectors** - S1, S2, S3 breakdown
- **Telemetry** - Speed, RPM, DRS, brakes
- **Issues** - Exactly where time was lost with estimates
- **Highlights** - What the driver did well
- **Comparison** - vs previous lap & vs best

### Performance Summary

At a glance:
- Best lap time
- Average lap time
- Total laps
- Personal bests
- Average speeds

## File Structure

```
/Users/gary/f1/react-dashboard/
├── src/
│   ├── components/
│   │   ├── views/
│   │   │   ├── PerformanceView.jsx
│   │   │   ├── TelemetryView.jsx
│   │   │   ├── ComparisonView.jsx
│   │   │   └── LapAnalysisView.jsx          ← NEW
│   │   └── analysis/
│   │       ├── LapTimeline.jsx               ← NEW
│   │       ├── LapDetailCard.jsx             ← NEW
│   │       └── PerformanceSummary.jsx        ← NEW
│   └── styles/
│       ├── lap-analysis-view.css             ← NEW
│       ├── lap-timeline.css                  ← NEW
│       ├── lap-detail-card.css               ← NEW
│       └── performance-summary.css           ← NEW
└── public/
    └── data/
        └── reports/                          ← COPY HERE
            ├── VER_Qualifying_laps.json
            ├── VER_Qualifying_laps.md
            └── ...
```

## Data Format

Analysis reports are JSON:

```json
{
  "metadata": {
    "driver": "VER",
    "session": "Qualifying",
    "circuit": "Austin",
    "year": 2024
  },
  "summary": {
    "best_lap_time": 92.143,
    "average_lap_time": 92.5,
    "total_laps": 14,
    "total_pbs": 12
  },
  "lap_analysis": [
    {
      "lap_number": 5,
      "lap_time_seconds": 92.807,
      "sectors": {"S1": 30.123, "S2": 31.456, "S3": 31.228},
      "telemetry": {
        "max_speed": 314.5,
        "avg_speed": 289.2,
        "drs_activations": 2,
        "brake_events": 8
      },
      "analysis": {
        "performance_assessment": "🟢 Best lap - Excellent",
        "issues": [
          {
            "category": "No DRS Activations",
            "severity": "High",
            "estimated_time_loss": "0.3-0.7s"
          }
        ],
        "highlights": [
          {
            "category": "Strong Sector 1",
            "description": "S1: 30.123s"
          }
        ]
      }
    }
  ]
}
```

## Complete Workflow

### One-Time Setup

```bash
# 1. Install Analysis Engine dependencies
cd /Users/gary/f1/analysis_engine
pip install -r requirements.txt

# 2. Install React Dashboard dependencies
cd /Users/gary/f1/react-dashboard
npm install

# 3. Create reports directory
mkdir -p /Users/gary/f1/react-dashboard/public/data/reports
```

### Generate and View Analysis

```bash
# 1. Generate fresh reports
cd /Users/gary/f1/analysis_engine
python main.py --all

# 2. Copy to dashboard
cp reports/* /Users/gary/f1/react-dashboard/public/data/reports/

# 3. Start dashboard
cd /Users/gary/f1/react-dashboard
npm run dev

# 4. Open in browser
# http://localhost:3001
# → Select driver
# → Click "⏱️ Analysis" tab
# → Explore lap-by-lap data!
```

## UI Navigation

```
Dashboard
├── Sidebar
│   ├── 📊 Dashboard        (current view)
│   ├── 📈 Telemetry
│   ├── ⚔️ Compare
│   └── ⏱️ Analysis          ← CLICK HERE
│
│   Driver Selection (20 drivers)
│   Session Filter (Q, SQ, S)
│
└── Main Area
    └── Analysis View
        ├── Performance Summary (top left)
        │   ├─ Best Lap
        │   ├─ Avg Lap
        │   ├─ Total Laps
        │   └─ Personal Bests
        │
        ├── Lap Timeline (left, scrollable)
        │   [L1] [L2] [L3⭐] [L4] [L5⚠️]
        │   Click any lap to see details
        │
        └── Lap Details (right, large)
            ├─ Lap Time
            ├─ Sectors (S1/S2/S3)
            ├─ Telemetry (Speed/RPM/DRS/Brakes)
            ├─ Tire Info
            ├─ 🔴 Issues (with time loss estimates)
            ├─ 🟢 Highlights
            └─ vs Previous Lap
```

## Troubleshooting

### Reports Not Found

```
Error: "No analysis data available"
```

**Solution:**
1. Check reports exist: `ls /Users/gary/f1/analysis_engine/reports/`
2. Copy to dashboard: `cp reports/* /Users/gary/f1/react-dashboard/public/data/reports/`
3. Refresh browser: Ctrl+R

### Data Not Loading

```
Error: "Failed to load lap data"
```

**Solution:**
1. Check network tab in browser DevTools
2. Verify file path is correct
3. Check file exists: `ls public/data/reports/`

### Browser Console Errors

Check browser console (F12) for:
- 404 errors = file not found
- JSON errors = corrupted data
- Permission errors = file access issue

## Advanced Usage

### Regenerate Reports on Demand

```bash
# In analysis_engine directory
python main.py --all --circuit "Austin" --year 2024

# Then copy
cp reports/* /Users/gary/f1/react-dashboard/public/data/reports/

# Refresh dashboard
# (Browser auto-refreshes on file changes with Vite)
```

### Analyze Different Events

```bash
cd /Users/gary/f1/analysis_engine

# Monaco 2024
python main.py --all --circuit "Monaco"

# Suzuka 2025 (when available)
python main.py --all --circuit "Suzuka" --year 2025

# Then copy and view in dashboard
cp reports/* /Users/gary/f1/react-dashboard/public/data/reports/
```

### Filter Specific Drivers

Edit `LapAnalysisView.jsx` to show only certain drivers:

```javascript
// Show only top 3 drivers
const topDrivers = ['VER', 'LEC', 'PIA'];

if (!topDrivers.includes(selectedDriver)) {
  return <div>Select one of the top drivers</div>;
}
```

## Performance Tips

- **First load**: May take 2-3 seconds (loading JSON)
- **Subsequent loads**: Instant (browser cache)
- **Scrolling timeline**: Smooth even with many laps
- **Large sessions**: Fine with 20+ laps

## Next Steps

1. ✅ Generate reports: `cd analysis_engine && python main.py --all`
2. ✅ Copy reports: `cp reports/* ../react-dashboard/public/data/reports/`
3. ✅ Start dashboard: `cd react-dashboard && npm run dev`
4. ✅ Open: `http://localhost:3001`
5. ✅ Click ⏱️ Analysis tab
6. ✅ Explore lap-by-lap data!

## Features Summary

### What You Can See

✅ Every lap a driver completed
✅ Exact time for each lap
✅ Sector-by-sector breakdown
✅ Telemetry data (speed, RPM, DRS, brakes)
✅ Tire compound and age
✅ Performance assessment (🟢/🟡/🔴)
✅ Specific issues with time loss estimates
✅ Highlights (what went right)
✅ Comparison to previous lap
✅ Comparison to best lap

### Analysis Insights

🔍 **Where did the driver lose time?**
- Tire degradation → 0.3s lost
- DRS issues → 0.5s lost
- Over-braking → 0.2s lost

📈 **How did they improve?**
- Lap 5: +0.5s vs Lap 4
- Trend: Getting faster
- Best lap achieved

⚙️ **Technical performance**
- Speed management
- Throttle control
- Braking efficiency
- DRS strategy

## Support

For issues:
1. Check `/Users/gary/f1/analysis_engine/README.md`
2. View example reports in `/Users/gary/f1/analysis_engine/reports/`
3. Check React components in `src/components/analysis/`

---

**Ready?** Follow the "Complete Workflow" section above! 🏁
