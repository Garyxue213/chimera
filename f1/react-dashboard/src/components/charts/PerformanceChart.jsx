import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function PerformanceChart({ drivers }) {
  const chartData = useMemo(() => {
    if (!drivers) return null;

    const sorted = Object.entries(drivers)
      .map(([id, data]) => ({
        id,
        rating: data?.executive_summary?.avg_performance_rating || 0,
      }))
      .sort((a, b) => b.rating - a.rating)
      .slice(0, 15);

    const getColor = (rating) => {
      if (rating >= 8) return 'rgba(74, 222, 128, 0.7)';
      if (rating >= 7) return 'rgba(96, 165, 250, 0.7)';
      if (rating >= 5) return 'rgba(251, 191, 36, 0.7)';
      return 'rgba(248, 113, 113, 0.7)';
    };

    return {
      labels: sorted.map(d => d.id),
      datasets: [
        {
          label: 'Performance Rating',
          data: sorted.map(d => d.rating),
          backgroundColor: sorted.map(d => getColor(d.rating)),
          borderColor: sorted.map(d =>
            d.rating >= 8 ? 'rgb(74, 222, 128)' :
            d.rating >= 7 ? 'rgb(96, 165, 250)' :
            d.rating >= 5 ? 'rgb(251, 191, 36)' :
            'rgb(248, 113, 113)'
          ),
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    };
  }, [drivers]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#ff6b35',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: (context) => `Rating: ${context.parsed.x.toFixed(1)}/10`,
        },
      },
    },
    scales: {
      x: {
        max: 10,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
          drawBorder: false,
        },
        ticks: {
          color: '#a0a0a0',
          font: {
            size: 12,
          },
        },
      },
      y: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#e0e0e0',
          font: {
            size: 12,
            weight: 600,
          },
        },
      },
    },
  };

  if (!chartData) return <div>No data available</div>;

  return (
    <div style={{ height: 300 }}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
