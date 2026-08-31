import { useRef, useEffect, useState, useCallback } from 'react'

const ZONE_ANGLES = {
  1: { x: 0.6, y: -0.8 }, 2: { x: 1.0, y: 0.0 }, 3: { x: 0.7, y: 0.7 }, 4: { x: 0.0, y: 1.0 },
  5: { x: -0.7, y: 0.7 }, 6: { x: -1.0, y: 0.0 }, 7: { x: -0.8, y: -0.6 }, 8: { x: -0.6, y: -0.8 },
}

const FIELD_LABELS = [
  { name: 'Square Leg', angle: 0 },
  { name: 'Mid Wicket', angle: 35 },
  { name: 'Mid On', angle: 70 },
  { name: 'Straight', angle: 90 },
  { name: 'Mid Off', angle: 110 },
  { name: 'Cover', angle: 145 },
  { name: 'Point', angle: 180 },
  { name: 'Backward Point', angle: 205 },
  { name: 'Third Man', angle: 235 },
  { name: 'Fine Leg', angle: 305 },
]

function getColor(runs, isWicket) {
  if (isWicket) return '#ff0000'
  if (runs === 0) return 'rgba(255,255,255,0.3)'
  if (runs === 4) return '#3b82f6'
  if (runs === 6) return '#ef4444'
  return '#facc15'
}

function pointToLineDistance(px, py, x1, y1, x2, y2) {
  const A = px - x1, B = py - y1, C = x2 - x1, D = y2 - y1
  const dot = A * C + B * D
  const lenSq = C * C + D * D
  let param = lenSq !== 0 ? dot / lenSq : -1
  let xx, yy
  if (param < 0) { xx = x1; yy = y1 }
  else if (param > 1) { xx = x2; yy = y2 }
  else { xx = x1 + param * C; yy = y1 + param * D }
  return Math.sqrt((px - xx) ** 2 + (py - yy) ** 2)
}

export default function WagonWheel({ data = [] }) {
  const canvasRef = useRef(null)
  const tooltipRef = useRef(null)
  const [filter, setFilter] = useState('All')
  const spokesRef = useRef([])

  const maxRun = Math.max(0, ...data.map((w) => w.runs || 0))
  const hasWickets = data.some((w) => w.is_wicket)

  const draw = useCallback((progress = 1.0) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2
    const radius = Math.min(centerX, centerY) - 20
    const batOriginY = centerY - radius * 0.134

    // Grass
    ctx.fillStyle = '#22c55e'
    ctx.fillRect(0, 0, width, height)
    ctx.fillStyle = '#16a34a'
    for (let i = 0; i < height; i += 40) ctx.fillRect(0, i, width, 20)

    // Boundary
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI)
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.stroke()

    // 30 yard circle
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius * 0.55, 0, 2 * Math.PI)
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Pitch
    const pitchW = 24, pitchH = 70
    ctx.fillStyle = '#eab308'
    ctx.fillRect(centerX - pitchW / 2, centerY - pitchH / 2, pitchW, pitchH)

    // Creases
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(centerX - pitchW / 2, centerY - pitchH / 2 + 12)
    ctx.lineTo(centerX + pitchW / 2, centerY - pitchH / 2 + 12)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(centerX - pitchW / 2, centerY + pitchH / 2 - 12)
    ctx.lineTo(centerX + pitchW / 2, centerY + pitchH / 2 - 12)
    ctx.stroke()

    // Labels
    ctx.font = '11px "Outfit", sans-serif'
    ctx.fillStyle = 'rgba(255,255,255,0.7)'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const labelR = radius + 1
    FIELD_LABELS.forEach((l) => {
      const a = (l.angle * Math.PI) / 180
      ctx.fillText(l.name, centerX - Math.cos(a) * labelR, centerY + Math.sin(a) * labelR)
    })

    // Spokes
    const drawn = []
    data.forEach((w) => {
      if (filter !== 'All') {
        if (filter === 'Wicket' ? !w.is_wicket : w.runs !== filter) return
      }

      let nx, ny
      if (w.x > 0 || w.y > 0) {
        nx = w.x / 180 - 1.0
        ny = w.y / 180 - 1.0
      } else if (w.zone > 0 && ZONE_ANGLES[w.zone]) {
        nx = ZONE_ANGLES[w.zone].x
        ny = ZONE_ANGLES[w.zone].y
      } else return

      const currentR = radius * progress
      const mappedX = centerX + nx * currentR
      const mappedY = centerY + ny * currentR

      ctx.beginPath()
      ctx.moveTo(centerX, batOriginY)
      ctx.lineTo(mappedX, mappedY)
      ctx.strokeStyle = getColor(w.runs, w.is_wicket)
      ctx.lineWidth = w.runs >= 4 ? 2.5 : 1.5
      ctx.stroke()

      drawn.push({ endX: mappedX, endY: mappedY, data: w })
    })
    spokesRef.current = drawn
  }, [data, filter])

  // Animation on filter change
  useEffect(() => {
    let progress = 0
    let frameId
    function animate() {
      progress += 0.05
      if (progress >= 1.0) {
        draw(1.0)
      } else {
        draw(progress)
        frameId = requestAnimationFrame(animate)
      }
    }
    animate()
    return () => { if (frameId) cancelAnimationFrame(frameId) }
  }, [draw])

  function handleMouseMove(e) {
    const canvas = canvasRef.current
    const tooltip = tooltipRef.current
    if (!canvas || !tooltip) return

    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    const mx = (e.clientX - rect.left) * scaleX
    const my = (e.clientY - rect.top) * scaleY
    const centerX = canvas.width / 2

    let closest = null
    let minDist = 12
    spokesRef.current.forEach((spoke) => {
      const d = pointToLineDistance(mx, my, centerX, canvas.height / 2 - (Math.min(centerX, canvas.height / 2) - 20) * 0.134, spoke.endX, spoke.endY)
      if (d < minDist) { minDist = d; closest = spoke }
    })

    if (closest) {
      tooltip.style.display = 'block'
      let leftPos = e.clientX + 15
      let topPos = e.clientY + 15
      if (leftPos + 200 > window.innerWidth) leftPos = e.clientX - 210
      if (topPos + 150 > window.innerHeight) topPos = e.clientY - 160
      tooltip.style.left = leftPos + 'px'
      tooltip.style.top = topPos + 'px'

      const w = closest.data
      let runColor = getColor(w.runs, w.is_wicket)
      tooltip.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">
          <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:${runColor};"></span>
          <span style="font-weight:600; font-size:1rem;">${w.runs} Runs</span>
        </div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Shot: <span style="color:white; font-weight:500;">${w.shot_type && w.shot_type !== 'Unknown' ? w.shot_type : 'Not Specified'}</span></div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Bowler: <span style="color:white; font-weight:500;">${w.bowler_name || 'Unknown'}</span></div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Length: <span style="color:white; font-weight:500;">${w.length || 'Unknown'}</span></div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Line: <span style="color:white; font-weight:500;">${w.line || 'Unknown'}</span></div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Over: <span style="color:white; font-weight:500;">${w.over - 1}${w.ball > 0 ? '.' + w.ball : ''}</span></div>
        <div style="margin-bottom:4px; color:var(--text-secondary);">Date: <span style="color:white; font-weight:500;">${w.date ? new Date(w.date).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' }) : 'Unknown'}</span></div>
      `
      canvas.style.cursor = 'pointer'
    } else {
      tooltip.style.display = 'none'
      canvas.style.cursor = 'default'
    }
  }

  const buttons = [{ label: 'All', value: 'All' }]
  for (let r = 1; r <= maxRun; r++) {
    if (data.some((w) => w.runs === r)) {
      buttons.push({ label: `${r} Run${r > 1 ? 's' : ''}`, value: r })
    }
  }
  if (hasWickets) buttons.push({ label: 'Wicket', value: 'Wicket' })

  if (data.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
        No wagon wheel data available
      </div>
    )
  }

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', width: '100%' }}>
        {buttons.map((b) => (
          <button
            key={b.value}
            className="filter-btn"
            style={{
              padding: '0.3rem 0.6rem', borderRadius: '4px', cursor: 'pointer',
              fontFamily: '"Outfit"', fontSize: '0.8rem', transition: 'all 0.2s',
              border: `1px solid ${filter === b.value ? 'var(--accent-blue)' : 'rgba(255,255,255,0.2)'}`,
              background: filter === b.value ? 'var(--accent-blue)' : 'rgba(255,255,255,0.05)',
              color: 'white',
            }}
            onClick={() => setFilter(b.value)}
          >
            {b.label}
          </button>
        ))}
      </div>
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
        <canvas
          ref={canvasRef}
          width={600}
          height={600}
          style={{ width: '100%', maxWidth: '500px', aspectRatio: '1/1' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { if (tooltipRef.current) tooltipRef.current.style.display = 'none' }}
        />
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem', width: '100%', fontSize: '0.85rem', color: 'white', fontFamily: "'Outfit'" }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ width: 16, height: 8, background: '#facc15', display: 'inline-block' }}></span> 1-3 Runs</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ width: 16, height: 8, background: '#3b82f6', display: 'inline-block' }}></span> 4 Runs</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ width: 16, height: 8, background: '#ef4444', display: 'inline-block' }}></span> 6 Runs</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ width: 16, height: 8, background: '#ff0000', display: 'inline-block' }}></span> Wicket</div>
        </div>
      </div>
      <div
        ref={tooltipRef}
        style={{
          position: 'fixed', display: 'none', background: 'rgba(15,23,42,0.95)',
          border: '1px solid rgba(255,255,255,0.1)', padding: '1rem', borderRadius: '8px',
          pointerEvents: 'none', zIndex: 1000, fontFamily: '"Outfit", sans-serif',
          fontSize: '0.85rem', color: 'white', boxShadow: '0 8px 16px rgba(0,0,0,0.5)',
          backdropFilter: 'blur(4px)', minWidth: '150px',
        }}
      />
    </>
  )
}
