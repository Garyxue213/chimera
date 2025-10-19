# 🏁 F1 Performance Dashboard - React

A modern, interactive React-based dashboard for F1 performance analysis with advanced visualizations and an animated telemetry viewer.

## Features

### 📊 Dashboard View
- Real-time performance statistics (rating, PBs, lap times, max speed)
- Driver rankings with performance charts
- Session-based performance breakdown
- Comprehensive driver profile with telemetry highlights
- Responsive grid layout

### 📡 Telemetry View
- **Animated Racetrack**: Real-time visualization of driver position on track
- Speed traces and lap data visualization
- Playback controls (play/pause)
- Variable replay speed (0.5x - 3x)
- Live telemetry data overlay
- Session-by-session performance breakdown

### ⚔️ Comparison View
- Head-to-head driver comparison
- Performance metrics side-by-side
- Comparative charts with multiple drivers
- Difference highlighting (advantages/disadvantages)

## Installation & Setup

### Prerequisites
- Node.js 16+
- npm or yarn

### Quick Start

```bash
# Install dependencies
npm install

# Start development server (opens on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
react-dashboard/
├── src/
│   ├── components/
│   │   ├── views/
│   │   │   ├── PerformanceView.jsx      # Main dashboard
│   │   │   ├── TelemetryView.jsx        # Telemetry visualization
│   │   │   └── ComparisonView.jsx       # Driver comparison
│   │   ├── charts/
│   │   │   ├── PerformanceChart.jsx     # Rankings chart
│   │   │   ├── SessionChart.jsx         # Session breakdown
│   │   │   └── ComparisonChart.jsx      # Comparison chart
│   │   ├── telemetry/
│   │   │   ├── AnimatedRacetrack.jsx    # Canvas animation
│   │   │   └── TelemetryStats.jsx       # Live stats display
│   │   ├── Dashboard.jsx                 # Main dashboard component
│   │   ├── Sidebar.jsx                   # Driver selection sidebar
│   │   ├── DriverProfile.jsx             # Profile card
│   │   └── StatCard.jsx                  # Stat display card
│   ├── styles/
│   │   ├── global.css                   # Global styles & theme
│   │   ├── app.css                      # App layout
│   │   ├── sidebar.css                  # Sidebar styling
│   │   ├── dashboard.css                # Dashboard layout
│   │   ├── stat-card.css                # Stat cards
│   │   ├── driver-profile.css           # Profile styling
│   │   ├── views.css                    # View layouts
│   │   ├── telemetry-view.css           # Telemetry view layout
│   │   ├── animated-racetrack.css       # Racetrack animation
│   │   ├── telemetry-stats.css          # Stats display
│   │   └── comparison-view.css          # Comparison layout
│   ├── App.jsx                           # Main app component
│   └── main.jsx                          # React entry point
├── index.html                            # HTML template
├── vite.config.js                        # Vite configuration
├── package.json                          # Dependencies
└── README.md                             # This file
```

## Key Components

### AnimatedRacetrack
Canvas-based animation showing:
- Real-time track visualization
- Driver position and speed traces
- Lap-by-lap data playback
- Performance overlay

```jsx
<AnimatedRacetrack
  driver={driver}
  driverId="LEC"
  isAnimating={true}
  speed={1}
/>
```

### PerformanceChart
Horizontal bar chart showing driver rankings with color-coded performance levels.

### TelemetryStats
Live display of:
- Max/average speeds
- DRS events
- Session performance breakdown
- Performance insights

## Usage

### Selecting a Driver
1. Click any driver card in the sidebar
2. View their profile and stats
3. Switch between Dashboard, Telemetry, and Comparison views

### Viewing Telemetry
1. Click the "📡 Telemetry" tab
2. Use Play/Pause to control animation
3. Adjust replay speed with the slider
4. Watch the animated racetrack simulation

### Comparing Drivers
1. Click the "⚔️ Compare" tab
2. Select a comparison driver from the dropdown
3. View detailed metrics side-by-side
4. See comparative performance chart

## Data Source

The dashboard reads from:
```
../data/driver_reports/all_drivers_summary.json
```

Includes data for 20 drivers across 3 sessions (Qualifying, Sprint Qualifying, Sprint Race).

## Technologies

- **React 18** - UI framework
- **Vite 5** - Build tool
- **Chart.js 4** - Data visualization
- **Canvas API** - Racetrack animation
- **CSS3** - Styling with CSS Grid/Flexbox

## Color Coding

- 🟢 **Green** - Exceptional (8.0+/10)
- 🔵 **Blue** - Strong (7.0-7.99/10)
- 🟡 **Yellow** - Consistent (5.0-6.99/10)
- 🔴 **Red** - Developing (<5.0/10)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Performance

- Fast load times (<1s)
- Smooth 60fps animations
- Responsive on all device sizes
- Optimized Canvas rendering

## Future Enhancements

- [ ] Export data to CSV
- [ ] Advanced filtering options
- [ ] Lap-by-lap telemetry data
- [ ] Real-time data connection
- [ ] Custom track layouts
- [ ] Sector analysis
- [ ] Weather data integration
- [ ] Multi-driver comparison

## License

MIT

---

**Created:** October 2025
**For:** Austin US Grand Prix 2025 Analysis
