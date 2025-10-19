# 🚀 F1 React Dashboard - Setup Guide

## One-Command Setup

```bash
cd /Users/gary/f1/react-dashboard && npm install && npm run dev
```

## Step-by-Step Setup

### 1. Install Dependencies
```bash
cd /Users/gary/f1/react-dashboard
npm install
```

This will install:
- React 18.2.0
- React DOM 18.2.0
- Chart.js 4.4.0
- React-ChartJS-2 5.2.0
- Zustand 4.4.0
- Vite 5.0.0
- Vite React Plugin

### 2. Start Development Server
```bash
npm run dev
```

The dashboard will automatically open at `http://localhost:3000`

### 3. Explore the Dashboard

#### Dashboard Tab (📊)
- View selected driver's performance stats
- See rankings of all drivers
- Check session breakdowns
- View detailed driver profile

#### Telemetry Tab (📡)
- Watch animated racetrack simulation
- Control playback speed
- View live telemetry data
- Track position and speed

#### Comparison Tab (⚔️)
- Select drivers to compare
- View side-by-side metrics
- See comparative performance chart

### 4. Build for Production
```bash
npm run build
```

Output will be in `dist/` directory

## File Structure

```
react-dashboard/
├── src/
│   ├── components/       # React components
│   ├── styles/          # CSS files
│   ├── App.jsx
│   └── main.jsx
├── index.html           # HTML template
├── vite.config.js       # Vite config
├── package.json         # Dependencies
└── README.md
```

## Troubleshooting

### Port Already in Use
If port 3000 is already in use:
```bash
npm run dev -- --port 3001
```

### Module Not Found Errors
Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Data Not Loading
Ensure the JSON file exists at:
```
/Users/gary/f1/data/driver_reports/all_drivers_summary.json
```

### Canvas Animation Not Working
Try a different browser (Chrome/Firefox usually work best for Canvas)

## Features to Try

1. **Click a driver** in the sidebar to load their data
2. **Search** for a driver by typing in the search box
3. **Filter by session** using the session dropdown
4. **Switch views** using the tab buttons
5. **Play the telemetry** animation and adjust speed
6. **Compare drivers** by selecting them in the comparison view

## Performance Tips

- The dashboard is optimized for 1920x1080+ on desktop
- Works great on laptops (1366x768+)
- Responsive design adapts to smaller screens
- Animations run at 60fps

## API/Data

The dashboard reads from:
```
../data/driver_reports/all_drivers_summary.json
```

Contains:
- 20 F1 drivers
- 224 strategic laps analyzed
- 3 sessions per driver
- Telemetry data (speeds, DRS events)
- Performance ratings

## Next Steps

1. ✅ Start the dev server
2. 🚗 Select a driver
3. 📊 Explore the dashboard
4. 📡 Watch the telemetry animation
5. ⚔️ Compare drivers
6. 📈 Build and deploy

---

**Happy exploring!** 🏁
