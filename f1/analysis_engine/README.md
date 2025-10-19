# 🏁 F1 Comprehensive Analysis Engine

A complete system for fetching real F1 telemetry data, analyzing with AI, and generating detailed lap-by-lap reports with timestamps.

## Overview

This engine provides:

✅ **Real F1 Data** - Fetches actual telemetry from FastF1
✅ **Lap-by-Lap Analysis** - Detailed breakdown of each lap
✅ **AI Insights** - Gemini AI analyzes performance issues
✅ **Timestamped Reports** - Exact moments where time was lost/gained
✅ **Performance Metrics** - Speed, RPM, DRS, tire data
✅ **Formatted Reports** - JSON + Markdown outputs

## Architecture

```
┌─────────────────────────────────┐
│  FastF1 Data Fetcher            │  Fetches real F1 telemetry
│  (fastf1_fetcher.py)            │  → 20 drivers, 3 sessions
└──────────────┬──────────────────┘
               │
               ▼
        ┌──────────────┐
        │   F1 Data    │  Austin 2024 complete dataset
        │   JSON File  │  224 laps with full telemetry
        └──────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Report Generator               │  Processes telemetry
│  (report_generator.py)          │  → Identifies issues
│                                 │  → Calculates metrics
└──────────────┬──────────────────┘
               │
               ▼
        ┌──────────────┐
        │  Analysis    │  Lap-by-lap breakdown
        │  Reports     │  - Performance issues
        │  (JSON/MD)   │  - Highlights
        └──────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Gemini AI Analyzer             │  (Optional) Deep analysis
│  (gemini_analyzer.py)           │  with AI insights
└─────────────────────────────────┘
```

## Installation

### 1. Install Dependencies

```bash
cd /Users/gary/f1/analysis_engine
pip install -r requirements.txt
```

Required packages:
- `fastf1==0.6.10` - F1 telemetry data
- `google-generativeai==0.3.0` - Gemini AI (optional)
- `pandas==2.1.0` - Data processing
- `requests==2.31.0` - HTTP requests

### 2. Set up Gemini API (Optional)

```bash
# Get your API key from: https://makersuite.google.com/app/apikey
export GEMINI_API_KEY='your-api-key-here'
```

Without this, you'll still get full telemetry analysis reports, just without AI insights.

## Usage

### Basic Usage

```bash
# Check environment
python main.py --setup-check

# Fetch Austin 2024 data
python main.py --fetch

# Generate reports from existing data
python main.py --analyze ./f1_cache/austin_2024_complete.json

# Do everything
python main.py --all
```

### Advanced Usage

```bash
# Different circuit and year
python main.py --all --year 2025 --circuit "Monaco"

# Custom cache directory
python main.py --fetch --cache-dir /custom/path/

# Only fetch data
python main.py --fetch --year 2024 --circuit "Austin"
```

## Output Structure

```
reports/
├── Qualifying_comparison.json          # Session comparison
├── Sprint_Qualifying_comparison.json   # All drivers ranked
├── Sprint_comparison.json
├── LEC_Qualifying_laps.json           # Per-driver detailed report
├── LEC_Qualifying_laps.md             # Formatted markdown
├── VER_Qualifying_laps.json
├── VER_Qualifying_laps.md
└── ... (all drivers, all sessions)
```

## Report Format

### Lap Entry Example

```json
{
  "lap_number": 5,
  "timestamp": "Lap 5 - 0:01:32.807",
  "lap_time_seconds": 92.807,
  "sectors": {
    "S1": 30.123,
    "S2": 31.456,
    "S3": 31.228
  },
  "tire": {
    "compound": "SOFT",
    "age": 3
  },
  "telemetry": {
    "max_speed": 314.5,
    "avg_speed": 289.2,
    "max_rpm": 15000,
    "drs_activations": 2,
    "brake_events": 8
  },
  "analysis": {
    "is_best_lap": true,
    "time_delta_from_best": "Best",
    "performance_assessment": "🟢 Best lap - Excellent performance",
    "issues": [
      {
        "category": "No DRS Activations",
        "description": "Failed to deploy DRS effectively",
        "severity": "High",
        "estimated_time_loss": "0.3-0.7s"
      }
    ],
    "highlights": [
      {
        "category": "Strong Sector 1",
        "description": "S1: 30.123s",
        "impact": "Excellent corner entry and mid-corner speed"
      }
    ]
  }
}
```

### Markdown Report Example

```markdown
# F1 Lap Analysis Report

## VER - Qualifying

### Lap 5 - 0:01:32.807

**Time:** 92.807s (Best)

**Sectors:**
- S1: 30.123s
- S2: 31.456s
- S3: 31.228s

**Telemetry:**
- Max Speed: 314.5 km/h
- Avg Speed: 289.2 km/h
- DRS Activations: 2
- Brake Events: 8

**Performance:** 🟢 Best lap - Excellent performance

**Issues:**
- **No DRS Activations** [High]: Failed to deploy DRS effectively (~0.3-0.7s lost)

**Highlights:**
- **Strong Sector 1**: S1: 30.123s - Excellent corner entry
```

## Data Fields Explained

### Telemetry
- **Max Speed**: Peak speed during lap (km/h)
- **Avg Speed**: Average speed (km/h)
- **Max RPM**: Peak engine RPM
- **DRS Activations**: Number of times DRS was deployed
- **Brake Events**: Number of braking instances

### Tire
- **Compound**: SOFT / MEDIUM / HARD / INTERMEDIATE
- **Age**: How many laps old the tire is

### Analysis Breakdown

**Performance Assessment:**
- 🟢 Best lap / Exceptional / Close to best
- 🟡 Good / Decent / Acceptable
- 🔴 Poor / Significant gap

**Issues Identified:**
- Tire Degradation (old tires)
- Low Average Speed (traffic/setup)
- No DRS Activations (positioning)
- Excessive Braking (aggressive braking)
- RPM Spike (throttle management)

**Highlights:**
- High Top Speed (good acceleration)
- Effective DRS Deployment (good race craft)
- Strong Sector 1/2/3 (excellent corner speed)

## Example Analysis

```
Lap 12 - VER (Sprint Race)

⏱️ LAP TIME: 113.456s
├─ S1: 32.123s
├─ S2: 41.234s
└─ S3: 40.099s

🔴 ISSUES:
├─ Tire Degradation (8 laps old) → ~0.3s lost
├─ Excessive Braking (12 events) → ~0.2s lost
└─ DRS Timing (only 1 activation) → ~0.4s lost
   Total Loss: ~0.9s

🟢 HIGHLIGHTS:
├─ Max Speed: 312 km/h (excellent)
└─ Strong S3: 40.099s (good exit speed)

📊 COMPARISON:
├─ Best Lap: 92.143s
├─ This Lap: 113.456s
└─ Difference: +21.313s (race conditions)
```

## Analyzing Results

### Per-Driver Insights

Open any `*_laps.md` file to see:
- Lap-by-lap performance
- Where time was lost (timestamped)
- Technical breakdown of issues
- Performance trends through session
- Best/worst sectors

### Session Comparison

Open `*_comparison.json` to see:
- Driver rankings
- Best lap times
- Consistency metrics
- Personal best counts
- Statistical insights

### Key Metrics to Watch

1. **Sector Times** - Identifies weak areas
2. **Tire Degradation** - How performance drops over lap life
3. **DRS Activations** - Race craft and positioning
4. **Brake Events** - Aggressive driving or mistakes
5. **Speed Trap** - Pure power/traction

## Integration with React Dashboard

The generated JSON reports can be loaded into your React dashboard:

```javascript
// React component
const [lapData, setLapData] = useState([]);

useEffect(() => {
  fetch('/data/reports/VER_Qualifying_laps.json')
    .then(res => res.json())
    .then(data => {
      setLapData(data.lap_analysis);
    });
}, []);

// Render lap-by-lap breakdown
lapData.forEach(lap => {
  console.log(`${lap.timestamp}: ${lap.analysis.performance_assessment}`);
  lap.analysis.issues.forEach(issue => {
    console.log(`  - ${issue.category}: ${issue.estimated_time_loss} lost`);
  });
});
```

## Advanced Features

### Gemini AI Analysis (Optional)

If `GEMINI_API_KEY` is set, the engine will also generate AI-powered insights:

```bash
python -c "from gemini_analyzer import GeminiF1Analyzer; analyzer = GeminiF1Analyzer(); print(analyzer.analyze_lap(...))"
```

This provides:
- Natural language performance analysis
- Technical breakdowns
- Comparison to teammate/competition
- Recommendations for improvement

### Custom Analysis

Modify `report_generator.py` to:
- Add more metrics
- Change issue detection
- Add custom highlights
- Integrate with external APIs

## Troubleshooting

### FastF1 Errors

```
# Data not available
Error: Session not found
→ Data available 30-120 minutes after session ends

# SSL Certificate Error
→ Update certificates: pip install --upgrade certifi
```

### API Errors

```
# GEMINI_API_KEY not found
→ Set environment variable: export GEMINI_API_KEY='...'

# Rate limit exceeded
→ Add delay between requests or use smaller batches
```

## Performance Tips

- First run takes 5-10 minutes (downloads all data)
- Subsequent runs use cache (< 1 minute)
- Clear cache with: `rm -rf f1_cache/`
- Process sessions individually for speed

## Next Steps

1. ✅ Install dependencies
2. ✅ Run `python main.py --all`
3. ✅ Check `reports/` directory
4. ✅ View markdown files for readable reports
5. ✅ Integrate into React dashboard
6. ✅ Customize analysis for your needs

## Resources

- **FastF1**: https://github.com/theOehrly/Fast-F1
- **Gemini API**: https://ai.google.dev/
- **F1 Data**: https://www.formula1.com/
- **Circuit Info**: https://en.wikipedia.org/wiki/Circuit_of_the_Americas

---

**Created:** October 2025
**For:** Austin US Grand Prix 3 Analysis
**Status:** Production Ready
