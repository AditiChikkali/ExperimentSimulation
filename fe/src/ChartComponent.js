import React, { useRef, useEffect } from 'react';
import Chart from 'chart.js/auto';

const ChartComponent = ({ data }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!Array.isArray(data)) {
      console.error('Expected data to be an array, but received:', data);
      return;
    }

    const ctx = chartRef.current.getContext('2d');

    if (chartInstance.current) {
      chartInstance.current.destroy(); // Destroy existing chart instance
    }

    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map((item) => new Date(item.time).toLocaleTimeString()), // X-axis labels
        datasets: [
          {
            label: 'Detector Reading',
            data: data.map((item) => item.det), // Y-axis data
            borderColor: 'blue',
            fill: false,
            tension: 0.4, // Makes the line smoother
          },
          {
            label: 'Motor Setpoint',
            data: data.map((item) => item.motor_setpoint),
            borderColor: 'red',
            fill: false,
            tension: 0.4, // Makes the line smoother
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Time',
            },
            ticks: {
              autoSkip: true,
              maxTicksLimit: 20,
            },
          },
          y: {
            title: {
              display: true,
              text: 'Value',
            },
            suggestedMin: 0, // Setting minimum value for better scaling
            suggestedMax: 60, // Setting maximum value for better scaling
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  return <canvas ref={chartRef}></canvas>;
};

export default ChartComponent;
