import React from 'react';
import '../../styles/lap-detail-card.css';

export default function LapDetailCard({ lap, bestLapTime }) {
  const timeDelta = lap.lap_time_seconds - bestLapTime;
  const timeDeltaStr = timeDelta === 0 ? 'Best' : `+${timeDelta.toFixed(3)}s`;

  return (
    <div className="lap-detail-card">
      <div className="lap-header">
        <h2>Lap {lap.lap_number}</h2>
        <div className="lap-time-display">
          <span className="lap-time">{lap.lap_time_seconds.toFixed(3)}s</span>
          <span className="lap-delta">{timeDeltaStr}</span>
        </div>
      </div>

      {/* Performance Assessment */}
      <div className="section">
        <h3>Performance</h3>
        <div className="assessment">
          <p>{lap.analysis.performance_assessment}</p>
        </div>
      </div>

      {/* Sectors */}
      <div className="section">
        <h3>Sector Times</h3>
        <div className="sectors-grid">
          <div className="sector">
            <span className="sector-label">S1</span>
            <span className="sector-time">{lap.sectors.S1.toFixed(3)}s</span>
          </div>
          <div className="sector">
            <span className="sector-label">S2</span>
            <span className="sector-time">{lap.sectors.S2.toFixed(3)}s</span>
          </div>
          <div className="sector">
            <span className="sector-label">S3</span>
            <span className="sector-time">{lap.sectors.S3.toFixed(3)}s</span>
          </div>
        </div>
      </div>

      {/* Telemetry */}
      <div className="section">
        <h3>Telemetry</h3>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="label">Max Speed</span>
            <span className="value">{lap.telemetry.max_speed} km/h</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Avg Speed</span>
            <span className="value">{lap.telemetry.avg_speed} km/h</span>
          </div>
          <div className="telemetry-item">
            <span className="label">DRS</span>
            <span className="value">{lap.telemetry.drs_activations}</span>
          </div>
          <div className="telemetry-item">
            <span className="label">Brakes</span>
            <span className="value">{lap.telemetry.brake_events}</span>
          </div>
        </div>
      </div>

      {/* Tire */}
      <div className="section">
        <h3>Tire</h3>
        <div className="tire-info">
          <span className="compound">{lap.tire.compound}</span>
          <span className="age">Age: {lap.tire.age} laps</span>
        </div>
      </div>

      {/* Issues */}
      {lap.analysis.issues && lap.analysis.issues.length > 0 && (
        <div className="section issues">
          <h3>🔴 Issues & Time Loss</h3>
          <div className="issues-list">
            {lap.analysis.issues.map((issue, idx) => (
              <div key={idx} className={`issue ${issue.severity.toLowerCase()}`}>
                <div className="issue-header">
                  <strong>{issue.category}</strong>
                  <span className="severity">{issue.severity}</span>
                </div>
                <p className="description">{issue.description}</p>
                <div className="time-loss">
                  ⏱️ Estimated Loss: <strong>{issue.estimated_time_loss}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Highlights */}
      {lap.analysis.highlights && lap.analysis.highlights.length > 0 && (
        <div className="section highlights">
          <h3>🟢 Highlights</h3>
          <div className="highlights-list">
            {lap.analysis.highlights.map((highlight, idx) => (
              <div key={idx} className="highlight">
                <div className="highlight-header">
                  <strong>{highlight.category}</strong>
                </div>
                <p className="description">{highlight.description}</p>
                <p className="impact">✓ {highlight.impact}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Previous Comparison */}
      {lap.analysis.comparison_to_previous && (
        <div className="section comparison">
          <h3>vs Previous Lap</h3>
          <div className="comparison-details">
            <div className="comp-item">
              <span className="label">Previous Time</span>
              <span className="value">
                {lap.analysis.comparison_to_previous.previous_lap_time}
              </span>
            </div>
            <div className="comp-item">
              <span className="label">Time Difference</span>
              <span className={`value ${lap.analysis.comparison_to_previous.time_difference.includes('-') ? 'faster' : 'slower'}`}>
                {lap.analysis.comparison_to_previous.time_difference}
              </span>
            </div>
            <div className="comp-item">
              <span className="label">Trend</span>
              <span className="value">
                {lap.analysis.comparison_to_previous.trend}
              </span>
            </div>
            <div className="comp-item">
              <span className="label">Tire Strategy</span>
              <span className="value">
                {lap.analysis.comparison_to_previous.tire_strategy}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
