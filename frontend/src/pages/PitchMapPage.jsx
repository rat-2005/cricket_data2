import { useState, useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'
import LoadingOverlay from '../components/LoadingOverlay'

Chart.register(...registerables)

export default function PitchMapPage() {
  const [bowler, setBowler] = useState('')
  const [batsman, setBatsman] = useState('')
  const [venue, setVenue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const chartRef = useRef(null)
  const canvasRef = useRef(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ is_wicket: 'false' })
      if (bowler) params.set('bowler', bowler)
      if (batsman) params.set('batsman', batsman)
      if (venue) params.set('venue', venue)

      const response = await fetch(`/api/stats/pitchmap_icc?${params.toString()}`)
      if (!response.ok) throw new Error('Failed to fetch data')
      const data = await response.json()
      
      renderChart(data)
    } catch (err) {
      console.error(err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const renderChart = (data) => {
    if (!canvasRef.current) return
    const ctx = canvasRef.current.getContext('2d')

    if (chartRef.current) {
      chartRef.current.destroy()
    }

    const points = data.map(ball => {
      if (!ball.ball_line_length) return null
      const parts = ball.ball_line_length.split(',')
      if (parts.length >= 2) {
        return {
          x: parseFloat(parts[0]),
          y: parseFloat(parts[1]),
          raw: ball
        }
      }
      return null
    }).filter(p => p !== null && !isNaN(p.x) && !isNaN(p.y))

    chartRef.current = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Deliveries',
          data: points,
          backgroundColor: 'rgba(52, 211, 153, 0.6)',
          borderColor: 'rgb(52, 211, 153)',
          borderWidth: 1,
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                const ball = ctx.raw.raw
                return [
                  `Speed: ${ball.ball_speed || 'N/A'} kph`,
                  `Bowler: ${ball.bowler_name}`,
                  `Batsman: ${ball.batsman_name}`,
                  `Wicket: ${ball.is_wicket ? 'Yes' : 'No'}`
                ]
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            title: { display: true, text: 'X Coordinate (Width)', color: '#94a3b8' },
            ticks: { color: '#64748b' }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.05)' },
            title: { display: true, text: 'Y Coordinate (Length)', color: '#94a3b8' },
            ticks: { color: '#64748b' }
          }
        }
      }
    })
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="container" style={{ maxWidth: 1200 }}>
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', background: 'linear-gradient(to right, #60a5fa, #34d399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          ICC Pitch Map Analytics
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>Advanced Ball Tracking & Line/Length Visualization</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '2rem' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', alignSelf: 'start' }}>
          <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Filters</h3>
          
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Bowler Name</label>
            <input type="text" value={bowler} onChange={(e) => setBowler(e.target.value)} placeholder="e.g. Bumrah" style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)', color: 'white' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Batsman Name</label>
            <input type="text" value={batsman} onChange={(e) => setBatsman(e.target.value)} placeholder="e.g. Kohli" style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)', color: 'white' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Venue</label>
            <input type="text" value={venue} onChange={(e) => setVenue(e.target.value)} placeholder="e.g. Wankhede" style={{ width: '100%', padding: '0.5rem', borderRadius: '8px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)', color: 'white' }} />
          </div>
          
          <button onClick={fetchData} style={{ marginTop: '1rem', background: 'linear-gradient(to right, #3b82f6, #10b981)', color: 'white', padding: '0.75rem', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
            Generate Pitch Map
          </button>
        </div>

        <div className="glass-panel" style={{ minHeight: 600, display: 'flex', flexDirection: 'column', position: 'relative' }}>
          <h2 style={{ marginBottom: '1rem' }}>Delivery Scatter Plot</h2>
          {error && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}
          <div style={{ flexGrow: 1, position: 'relative', background: '#1e293b', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', inset: '3rem', border: '2px solid rgba(16, 185, 129, 0.5)', background: 'rgba(139, 90, 43, 0.2)', pointerEvents: 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
               <div style={{ borderBottom: '2px solid rgba(255,255,255,0.2)', height: '3rem' }}></div>
               <div style={{ borderTop: '2px solid rgba(255,255,255,0.2)', height: '3rem' }}></div>
            </div>
            <canvas ref={canvasRef}></canvas>
          </div>
        </div>
      </div>
      <LoadingOverlay visible={loading} text="Loading Pitch Data..." />
    </div>
  )
}
