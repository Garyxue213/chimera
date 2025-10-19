import React, { useState, useEffect, useRef } from 'react';
import LapTimeline from '../analysis/LapTimeline';
import LapDetailCard from '../analysis/LapDetailCard';
import PerformanceSummary from '../analysis/PerformanceSummary';
import AudioPlayer from '../analysis/AudioPlayer';
import ElevenLabsService from '../../services/ElevenLabsService';
import '../../styles/lap-analysis-view.css';

export default function LapAnalysisView({
  drivers,
  selectedDriver,
  selectedSession,
}) {
  const [lapData, setLapData] = useState(null);
  const [selectedLap, setSelectedLap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [generatingAudio, setGeneratingAudio] = useState(false);
  const elevenLabsRef = useRef(new ElevenLabsService());

  useEffect(() => {
    loadLapData();
  }, [selectedDriver, selectedSession]);

  useEffect(() => {
    // Generate audio narration when lap is selected
    if (selectedLap && selectedLap.analysis) {
      generateLapNarration(selectedLap);
    }
  }, [selectedLap]);

  const generateLapNarration = async (lap) => {
    if (!lap.analysis) {
      setAudioUrl(null);
      return;
    }

    setGeneratingAudio(true);
    try {
      const audioBlob = await elevenLabsRef.current.narrateLapAnalysis(
        lap.analysis,
        lap
      );

      if (audioBlob) {
        const url = elevenLabsRef.current.createAudioUrl(audioBlob);
        setAudioUrl(url);
      } else {
        setAudioUrl(null);
      }
    } catch (error) {
      console.error('Failed to generate narration:', error);
      setAudioUrl(null);
    } finally {
      setGeneratingAudio(false);
    }
  };

  // Cleanup audio URLs on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        elevenLabsRef.current.revokeAudioUrl(audioUrl);
      }
    };
  }, []);

  const loadLapData = async () => {
    setLoading(true);
    setAudioUrl(null);
    try {
      // Map session names to file names
      const sessionMap = {
        'Qualifying': 'Qualifying',
        'Sprint Qualifying': 'Sprint_Qualifying',
        'Sprint Race': 'Sprint',
      };

      const sessionFile = sessionMap[selectedSession] || selectedSession;
      const fileName = `${selectedDriver}_${sessionFile}_laps.json`;

      const response = await fetch(`/data/reports/${fileName}`);
      if (response.ok) {
        const data = await response.json();
        setLapData(data);
        if (data.lap_analysis && data.lap_analysis.length > 0) {
          setSelectedLap(data.lap_analysis[0]);
        }
      } else {
        console.log(`Report not found: ${fileName}`);
        setLapData(null);
      }
    } catch (error) {
      console.error('Error loading lap data:', error);
      setLapData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="view-container">
        <div className="loading-message">Loading lap analysis data...</div>
      </div>
    );
  }

  if (!lapData) {
    return (
      <div className="view-container">
        <header className="view-header">
          <h1>⏱️ Lap-by-Lap Analysis</h1>
          <p className="view-subtitle">
            Detailed breakdown with issue identification and time loss analysis
          </p>
        </header>
        <div className="no-data">
          <p>No analysis data available for {selectedDriver}</p>
          <p className="note">Run the analysis engine to generate reports</p>
        </div>
      </div>
    );
  }

  return (
    <div className="view-container">
      <header className="view-header">
        <h1>⏱️ {selectedDriver} Lap Analysis - {selectedSession}</h1>
        <p className="view-subtitle">
          Lap-by-lap breakdown with performance issues and technical analysis
        </p>
      </header>

      <section className="analysis-container">
        <div className="analysis-left">
          {/* Performance Summary */}
          <PerformanceSummary
            summary={lapData.summary}
            metadata={lapData.metadata}
          />

          {/* Lap Timeline */}
          <LapTimeline
            laps={lapData.lap_analysis}
            selectedLap={selectedLap}
            onSelectLap={setSelectedLap}
          />
        </div>

        <div className="analysis-right">
          {/* Audio Narration Player */}
          {selectedLap && (
            <AudioPlayer
              audioUrl={audioUrl}
              isLoading={generatingAudio}
            />
          )}

          {/* Detailed Lap View */}
          {selectedLap && (
            <LapDetailCard
              lap={selectedLap}
              bestLapTime={lapData.summary.best_lap_time}
            />
          )}
        </div>
      </section>
    </div>
  );
}
