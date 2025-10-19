import React from 'react';
import PerformanceView from './views/PerformanceView';
import TelemetryView from './views/TelemetryView';
import ComparisonView from './views/ComparisonView';
import LapAnalysisView from './views/LapAnalysisView';
import RaceAnimatorView from './views/RaceAnimatorView';
import '../styles/dashboard.css';

export default function Dashboard({
  drivers,
  selectedDriver,
  selectedSession,
  view,
}) {
  return (
    <div className="dashboard">
      {view === 'dashboard' && (
        <PerformanceView
          drivers={drivers}
          selectedDriver={selectedDriver}
          selectedSession={selectedSession}
        />
      )}
      {view === 'telemetry' && (
        <TelemetryView
          drivers={drivers}
          selectedDriver={selectedDriver}
          selectedSession={selectedSession}
        />
      )}
      {view === 'comparison' && (
        <ComparisonView
          drivers={drivers}
          selectedDriver={selectedDriver}
          selectedSession={selectedSession}
        />
      )}
      {view === 'analysis' && (
        <LapAnalysisView
          drivers={drivers}
          selectedDriver={selectedDriver}
          selectedSession={selectedSession}
        />
      )}
      {view === 'race' && (
        <RaceAnimatorView />
      )}
    </div>
  );
}
