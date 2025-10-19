import React from 'react';
import '../styles/driver-profile.css';

export default function DriverProfile({ driver, driverId }) {
  const summary = driver?.executive_summary;
  const telemetry = driver?.telemetry_highlights;

  if (!summary) return null;

  const getPerformanceLabel = (rating) => {
    if (rating >= 8) return 'EXCEPTIONAL';
    if (rating >= 7) return 'STRONG';
    if (rating >= 5) return 'CONSISTENT';
    return 'DEVELOPING';
  };

  const getPerformanceColor = (rating) => {
    if (rating >= 8) return 'exceptional';
    if (rating >= 7) return 'strong';
    if (rating >= 5) return 'consistent';
    return 'developing';
  };

  return (
    <div className="driver-profile">
      <div className="profile-header">
        <div className="profile-title">
          <h2>{driverId} - Profile</h2>
          <span className={`performance-badge ${getPerformanceColor(summary.avg_performance_rating)}`}>
            {getPerformanceLabel(summary.avg_performance_rating)}
          </span>
        </div>
      </div>

      <div className="profile-grid">
        <div className="profile-section">
          <h3>Overall Performance</h3>
          <div className="profile-stats">
            <div className="stat">
              <span className="label">Performance Rating</span>
              <span className="value">{summary.avg_performance_rating.toFixed(1)}/10</span>
            </div>
            <div className="stat">
              <span className="label">Best Lap Time</span>
              <span className="value">{summary.best_lap_time.toFixed(3)}s</span>
            </div>
            <div className="stat">
              <span className="label">Personal Bests</span>
              <span className="value">{summary.personal_bests}</span>
            </div>
            <div className="stat">
              <span className="label">Deleted Laps</span>
              <span className="value">{summary.deleted_laps}</span>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h3>Telemetry</h3>
          <div className="profile-stats">
            <div className="stat">
              <span className="label">Max Speed Recorded</span>
              <span className="value">{telemetry?.max_speed_recorded.toFixed(0)} km/h</span>
            </div>
            <div className="stat">
              <span className="label">Average Max Speed</span>
              <span className="value">{telemetry?.avg_max_speed.toFixed(1)} km/h</span>
            </div>
            <div className="stat">
              <span className="label">Total DRS Events</span>
              <span className="value">{telemetry?.total_drs_events}</span>
            </div>
            <div className="stat">
              <span className="label">Avg DRS per Lap</span>
              <span className="value">{telemetry?.avg_drs_per_lap.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {driver?.session_breakdown && (
          <div className="profile-section full-width">
            <h3>Session Breakdown</h3>
            <div className="session-grid">
              {Object.entries(driver.session_breakdown).map(([sessionName, sessionData]) => (
                <div key={sessionName} className="session-card">
                  <h4>{sessionName}</h4>
                  <div className="session-stats">
                    <div className="mini-stat">
                      <span className="label">Laps</span>
                      <span className="value">{sessionData.laps_analyzed}</span>
                    </div>
                    <div className="mini-stat">
                      <span className="label">Best Time</span>
                      <span className="value">{sessionData.best_lap_time.toFixed(3)}s</span>
                    </div>
                    <div className="mini-stat">
                      <span className="label">Avg Time</span>
                      <span className="value">{sessionData.avg_lap_time.toFixed(3)}s</span>
                    </div>
                    <div className="mini-stat">
                      <span className="label">Rating</span>
                      <span className="value">{sessionData.avg_performance_rating.toFixed(1)}</span>
                    </div>
                    <div className="mini-stat">
                      <span className="label">PBs</span>
                      <span className="value">{sessionData.pbs_in_session}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {summary.sample_insights && (
          <div className="profile-section full-width">
            <h3>Sample Insights</h3>
            <ul className="insights-list">
              {summary.sample_insights.map((insight, idx) => (
                <li key={idx}>{insight}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
