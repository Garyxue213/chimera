import React, { useEffect, useRef, useState } from 'react';
import '../../styles/animated-racetrack.css';

export default function AnimatedRacetrack({
  driver,
  driverId,
  isAnimating,
  speed,
}) {
  const canvasRef = useRef(null);
  const [animationFrame, setAnimationFrame] = useState(0);
  const animationRef = useRef(null);

  // Generate a realistic F1 track layout
  const generateTrackPath = (width, height) => {
    const margin = 60;
    const innerWidth = width - margin * 2;
    const innerHeight = height - margin * 2;

    // Create a track outline (outer loop)
    const outer = new Path2D();
    outer.roundRect(margin, margin, innerWidth, innerHeight, 20);

    // Create track inner (inner loop)
    const inner = new Path2D();
    inner.roundRect(margin + 30, margin + 30, innerWidth - 60, innerHeight - 60, 15);

    return { outer, inner };
  };

  // Generate synthetic lap data based on driver telemetry
  const generateLapData = () => {
    const lapCount = Math.ceil(Math.random() * 20 + 10);
    const lapData = [];

    for (let i = 0; i < lapCount; i++) {
      const points = [];
      const maxSpeed = driver.telemetry_highlights?.max_speed_recorded || 200;

      for (let j = 0; j < 100; j++) {
        const angle = (j / 100) * Math.PI * 2;
        const speed = maxSpeed * (0.8 + Math.random() * 0.2);
        const variance = Math.sin(angle * 3) * 20;

        points.push({
          angle,
          speed: speed + variance,
          x: 200 + Math.cos(angle) * 100,
          y: 200 + Math.sin(angle) * 80,
        });
      }

      lapData.push({
        lapNumber: i + 1,
        points,
        totalTime: 92 + Math.random() * 5,
        avgSpeed: maxSpeed * 0.9,
      });
    }

    return lapData;
  };

  const lapData = useRef(generateLapData()).current;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    const animate = () => {
      // Clear canvas
      ctx.fillStyle = 'rgba(15, 15, 30, 0.9)';
      ctx.fillRect(0, 0, width, height);

      // Draw grid
      ctx.strokeStyle = 'rgba(255, 107, 53, 0.1)';
      ctx.lineWidth = 1;
      for (let i = 0; i < width; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
      }
      for (let i = 0; i < height; i += 40) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
      }

      // Draw track boundary
      ctx.strokeStyle = 'rgba(255, 107, 53, 0.5)';
      ctx.lineWidth = 3;
      ctx.strokeRect(50, 50, width - 100, height - 100);

      // Draw inner track
      ctx.strokeStyle = 'rgba(247, 147, 30, 0.3)';
      ctx.lineWidth = 2;
      ctx.strokeRect(100, 100, width - 200, height - 200);

      // Current lap
      const currentLap =
        lapData[Math.floor((animationFrame % (lapData.length * 100)) / 100)];
      const pointInLap = animationFrame % 100;

      if (currentLap) {
        // Draw lap line
        ctx.strokeStyle = 'rgba(96, 165, 250, 0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (let i = 0; i < currentLap.points.length; i++) {
          const point = currentLap.points[i];
          const x = 200 + Math.cos(point.angle) * 120;
          const y = 200 + Math.sin(point.angle) * 100;

          if (i === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        ctx.closePath();
        ctx.stroke();

        // Draw car position
        const currentPoint = currentLap.points[Math.floor(pointInLap)];
        const nextPoint = currentLap.points[Math.floor(pointInLap + 1) % currentLap.points.length];

        if (currentPoint) {
          const carX = 200 + Math.cos(currentPoint.angle) * 120;
          const carY = 200 + Math.sin(currentPoint.angle) * 100;

          // Car body
          ctx.fillStyle = '#ff6b35';
          ctx.beginPath();
          ctx.arc(carX, carY, 8, 0, Math.PI * 2);
          ctx.fill();

          // Car glow
          ctx.fillStyle = 'rgba(255, 107, 53, 0.4)';
          ctx.beginPath();
          ctx.arc(carX, carY, 15, 0, Math.PI * 2);
          ctx.fill();

          // Speed indicator line
          ctx.strokeStyle = 'rgba(255, 107, 53, 0.8)';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(carX, carY);
          const speedScale = (currentPoint.speed / 250) * 30;
          ctx.lineTo(
            carX + Math.cos(currentPoint.angle) * speedScale,
            carY + Math.sin(currentPoint.angle) * speedScale
          );
          ctx.stroke();
        }
      }

      // Draw stats overlay
      ctx.font = 'bold 14px sans-serif';
      ctx.fillStyle = '#ff6b35';
      ctx.fillText(`Driver: ${driverId}`, 20, 30);

      if (currentLap) {
        ctx.fillText(`Lap: ${currentLap.lapNumber}/${lapData.length}`, 20, 50);
        ctx.fillText(
          `Speed: ${(currentLap.points[pointInLap]?.speed || 0).toFixed(0)} km/h`,
          20,
          70
        );
        ctx.fillText(`Time: ${currentLap.totalTime.toFixed(3)}s`, 20, 90);
      }

      // Progress bar
      const progress = (animationFrame % (lapData.length * 100)) / (lapData.length * 100);
      ctx.fillStyle = 'rgba(255, 107, 53, 0.2)';
      ctx.fillRect(20, height - 30, width - 40, 10);
      ctx.fillStyle = '#ff6b35';
      ctx.fillRect(20, height - 30, (width - 40) * progress, 10);

      if (isAnimating) {
        setAnimationFrame(prev => prev + (speed || 1));
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [driverId, isAnimating, speed, lapData]);

  return (
    <div className="animated-racetrack">
      <canvas
        ref={canvasRef}
        width={600}
        height={400}
        className="racetrack-canvas"
      />
      <div className="racetrack-info">
        <p>Max Speed: {driver.telemetry_highlights?.max_speed_recorded} km/h</p>
        <p>Avg Speed: {driver.telemetry_highlights?.avg_max_speed.toFixed(1)} km/h</p>
        <p>DRS Events: {driver.telemetry_highlights?.total_drs_events}</p>
      </div>
    </div>
  );
}
