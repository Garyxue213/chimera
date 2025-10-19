import React from 'react';
import '../styles/stat-card.css';

export default function StatCard({
  label,
  value,
  unit = '',
  icon = '',
  color = 'exceptional',
}) {
  return (
    <div className={`stat-card ${color}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <h3 className="stat-label">{label}</h3>
        <div className="stat-value">
          <span className="stat-number">{value}</span>
          {unit && <span className="stat-unit">{unit}</span>}
        </div>
      </div>
    </div>
  );
}
