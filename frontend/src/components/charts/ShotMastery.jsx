import { useRef, useEffect, useState } from 'react'
import { Chart, registerables } from 'chart.js'
import { TreemapController, TreemapElement } from 'chartjs-chart-treemap'

Chart.register(...registerables, TreemapController, TreemapElement)

export default function ShotMastery({ shotData = {} }) {
  const canvasRef = useRef(null)
  const chartRef = useRef(null)
  const [metric, setMetric] = useState('cnt')

  const labels = Object.keys(shotData)
  const values = Object.values(shotData)

  useEffect(() => {
    if (!canvasRef.current || labels.length === 0) return

    if (chartRef.current) chartRef.current.destroy()

    const treeData = []
    const metricValues = values.map((v) => (typeof v === 'object' ? v[metric] || 0 : v))
    const maxVal = Math.max(...metricValues, 1)

    for (let i = 0; i < labels.length; i++) {
      const val = typeof values[i] === 'object' ? values[i][metric] || 0 : values[i]
      if (val > 0) treeData.push({ n: labels[i], v: val })
    }

    chartRef.current = new Chart(canvasRef.current, {
      type: 'treemap',
      data: {
        datasets: [{
          label: 'Shot Mastery',
          tree: treeData,
          key: 'v',
          groups: ['n'],
          backgroundColor: (ctx) => {
            if (ctx.type !== 'data') return 'transparent'
            const alpha = Math.min(1.0, 0.4 + (ctx.raw.v / maxVal) * 0.6)
            return `rgba(16, 185, 129, ${alpha})`
          },
          borderWidth: 1,
          borderColor: 'rgba(255,255,255,0.1)',
          labels: {
            display: true,
            font: { family: 'Outfit', size: 12 },
            color: '#ffffff',
            formatter: (ctx) => [ctx.raw.g, ctx.raw.v],
          },
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: () => '',
              label: (ctx) => `${ctx.raw.g}: ${ctx.raw.v}`,
            },
          },
        },
      },
    })

    return () => { if (chartRef.current) chartRef.current.destroy() }
  }, [shotData, metric])

  const metrics = [
    { key: 'cnt', label: 'Times Played' },
    { key: 'runs', label: 'Runs Scored' },
    { key: 'wickets', label: 'Wickets Lost' },
  ]

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', width: '100%' }}>
        {metrics.map((m) => (
          <button
            key={m.key}
            className="filter-btn"
            style={{
              padding: '0.3rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
              fontFamily: '"Outfit"', fontSize: '0.8rem', transition: 'all 0.2s',
              border: `1px solid ${metric === m.key ? 'var(--accent-green)' : 'rgba(255,255,255,0.2)'}`,
              background: metric === m.key ? 'var(--accent-green)' : 'rgba(255,255,255,0.05)',
              color: 'white',
            }}
            onClick={() => setMetric(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: 300, width: '100%' }}>
        <canvas ref={canvasRef}></canvas>
      </div>
    </>
  )
}
