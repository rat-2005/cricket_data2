import { useRef, useEffect } from 'react'
import { Chart, registerables } from 'chart.js'
Chart.register(...registerables)

export default function DismissalChart({ wicketData = {} }) {
  const canvasRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!canvasRef.current) return
    if (chartRef.current) chartRef.current.destroy()

    const labels = Object.keys(wicketData)
    const values = Object.values(wicketData)

    if (labels.length === 0) return

    chartRef.current = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Dismissals',
          data: values,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
          x: { grid: { display: false } },
        },
      },
    })

    return () => { if (chartRef.current) chartRef.current.destroy() }
  }, [wicketData])

  return <canvas ref={canvasRef}></canvas>
}
