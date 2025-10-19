import React from 'react';
import '../../styles/telemetry-stats.css';

export default function TelemetryStats({ driver, driverId, session }) {
  const telemetry = driver?.telemetry_highlights || {};
  const sessionData = driver?.session_breakdown || {};

  const allSessions = Object.entries(sessionData);
  const bestSession = allSessions.reduce((best, [name, data]) => {
    const current = {
      name,
      rating: data.avg_performance_rating,
      laps: data.laps_analyzed,
    };
    return current.rating > best.rating ? current : best;
  }, { name: '', rating: 0, laps: 0 });

  return (
    <div className="telemetry-stats">
      <div className="stats-section">
        <h3>Current Session Telemetry</h3>
        <div className="telemetry-grid">
          <div className="telemetry-item">
            <span className="telemetry-label">Max Speed</span>
            <span className="telemetry-value">{telemetry.max_speed_recorded?.toFixed(0) || '-'}</span>
            <span className="telemetry-unit">km/h</span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-label">Avg Speed</span>
            <span className="telemetry-value">{telemetry.avg_max_speed?.toFixed(1) || '-'}</span>
            <span className="telemetry-unit">km/h</span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-label">DRS Events</span>
            <span className="telemetry-value">{telemetry.total_drs_events || 0}</span>
            <span className="telemetry-unit">events</span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-label">Avg DRS/Lap</span>
            <span className="telemetry-value">{telemetry.avg_drs_per_lap?.toFixed(2) || '0'}</span>
            <span className="telemetry-unit">/lap</span>
          </div>
        </div>
      </div>

      {bestSession.name && (
        <div className="stats-section">
          <h3>Best Session Performance</h3>
          <div className="best-session">
            <div className="session-name">{bestSession.name}</div>
            <div className="session-details">
              <p>Rating: <strong>{bestSession.rating.toFixed(1)}/10</strong></p>
              <p>Laps: <strong>{bestSession.laps}</strong></p>
            </div>
          </div>
        </div>
      )}

      <div className="stats-section">
        <h3>All Sessions</h3>
        <div className="sessions-list">
          {allSessions.map(([sessionName, data]) => (
            <div key={sessionName} className="session-item">
              <div className="session-name-small">{sessionName}</div>
              <div className="session-bars">
                <div className="bar-container">
                  <span className="bar-label">Rating</span>
                  <div className="bar">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${(data.avg_performance_rating / 10) * 100}%`,
                        background:
                          data.avg_performance_rating >= 8
                            ? '#4ade80'
                            : data.avg_performance_rating >= 7
                            ? '#60a5fa'
                            : '#fbbf24',
                      }}
                    ></div>
                  </div>
                  <span className="bar-value">{data.avg_performance_rating.toFixed(1)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="stats-section">
        <h3>Performance Insights</h3>
        <ul className="insights">
          <li>
            <strong>Peak Performance:</strong> Session with highest rating
          </li>
          <li>
            <strong>Consistency:</strong> Similar performance across all sessions
          </li>
          <li>
            <strong>Speed Management:</strong> Optimal DRS deployment strategy
          </li>
          <li>
            <strong>Avg Rating:</strong> {driver.executive_summary?.avg_performance_rating.toFixed(1)}/10
          </li>
        </ul>
      </div>
    </div>
  );
}
