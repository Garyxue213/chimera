import React, { useState, useMemo } from 'react';
import AnimatedRacetrack from '../telemetry/AnimatedRacetrack';
import TelemetryStats from '../telemetry/TelemetryStats';
import '../../styles/telemetry-view.css';

export default function TelemetryView({
  drivers,
  selectedDriver,
  selectedSession,
}) {
  const [isAnimating, setIsAnimating] = useState(true);
  const [speed, setSpeed] = useState(1);

  const currentDriver = drivers[selectedDriver];

  if (!currentDriver) {
    return (
      <div className="view-container">
        <p>Select a driver to view telemetry data</p>
      </div>
    );
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>📡 {selectedDriver} Telemetry Analysis</h1>
        <p className="view-subtitle">
          Real-time telemetry data with animated racetrack visualization
        </p>
      </header>

      <div className="telemetry-controls">
        <button
          className={`control-btn ${isAnimating ? 'active' : ''}`}
          onClick={() => setIsAnimating(!isAnimating)}
        >
          {isAnimating ? '⏸️ Pause' : '▶️ Play'}
        </button>
        <div className="speed-control">
          <label htmlFor="speed-slider">Replay Speed:</label>
          <input
            id="speed-slider"
            type="range"
            min="0.5"
            max="3"
            step="0.5"
            value={speed}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            className="speed-slider"
          />
          <span className="speed-value">{speed}x</span>
        </div>
      </div>

      <div className="telemetry-grid">
        <div className="racetrack-section">
          <h2 className="section-title">Racetrack Simulation</h2>
          <AnimatedRacetrack
            driver={currentDriver}
            driverId={selectedDriver}
            isAnimating={isAnimating}
            speed={speed}
          />
        </div>

        <div className="telemetry-stats-section">
          <h2 className="section-title">Live Telemetry Data</h2>
          <TelemetryStats
            driver={currentDriver}
            driverId={selectedDriver}
            session={selectedSession}
          />
        </div>
      </div>
    </div>
  );
}
