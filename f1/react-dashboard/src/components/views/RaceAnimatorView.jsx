import React from 'react';
import '../../styles/race-animator-view.css';

export default function RaceAnimatorView() {
  return (
    <div className="view-container race-animator-container">
      <header className="view-header">
        <h1>🏁 Live Race Animator</h1>
        <p className="view-subtitle">
          Real-time race simulation with standings, circuit map, and telemetry
        </p>
      </header>

      <div className="animator-frame-container">
        <div className="frame-wrapper">
          <iframe
            src="http://localhost:3333"
            title="F1 Race Animator"
            className="race-animator-frame"
            allowFullScreen
          ></iframe>
        </div>

        <div className="animator-info">
          <h3>🏎️ Race Simulation Features</h3>
          <ul>
            <li>✅ Live driver standings with real-time updates</li>
            <li>✅ Interactive circuit map with driver positions</li>
            <li>✅ Real-time telemetry data display</li>
            <li>✅ Lap counter and session timing</li>
            <li>✅ Pit stop tracking</li>
            <li>✅ Speed playback controls</li>
          </ul>

          <h3 style={{marginTop: '20px'}}>⏱️ Controls</h3>
          <ul>
            <li>▶ Play - Start the race simulation</li>
            <li>↻ Reset - Return to lap 1</li>
            <li>Speed - Adjust playback speed (1x, 2x, 4x, etc.)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
