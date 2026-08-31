import { useState, useRef } from 'react'

const LENGTHS = ['FULL_TOSS', 'YORKER', 'FULL', 'GOOD_LENGTH', 'SHORT_OF_A_GOOD_LENGTH', 'SHORT']
const LENGTH_LABELS = ['Full Toss', 'Yorker', 'Full Length', 'Good Length', 'Short of good length', 'Short Length']
const LINES = ['WIDE_OUTSIDE_OFFSTUMP', 'OUTSIDE_OFFSTUMP', 'ON_THE_STUMPS', 'DOWN_LEG', 'WIDE_DOWN_LEG']

export default function PitchHeatmap({ data = [] }) {
  const tooltipRef = useRef(null)

  const map = {}
  let maxWickets = 0, maxRuns = 0
  data.forEach((d) => {
    if (!map[d.length]) map[d.length] = {}
    map[d.length][d.line] = d
    if (d.wickets > maxWickets) maxWickets = d.wickets
    if (d.runs > maxRuns) maxRuns = d.runs
  })
  const maxWGradient = maxWickets > 0 ? maxWickets : 1
  const maxRGradient = maxRuns > 0 ? maxRuns : 1

  function getTooltipText(cellData) {
    if (!cellData) return 'No data'
    let text = `Runs: ${cellData.runs} | Balls: ${cellData.balls} | Wickets: ${cellData.wickets}\n`
    if (cellData.runs > 0 && cellData.shots && Object.keys(cellData.shots).length > 0) {
      text += '\n-- Runs by Shot --\n'
      Object.entries(cellData.shots).sort((a, b) => b[1] - a[1]).forEach(([shot, r]) => {
        text += `${shot.charAt(0).toUpperCase() + shot.slice(1)}: ${r}\n`
      })
    }
    if (cellData.wickets > 0 && cellData.wicket_events?.length > 0) {
      text += '\n-- Wickets --\n'
      cellData.wicket_events.forEach((w) => { text += `• ${w.shot} → ${w.type}\n` })
    }
    return text.trim()
  }

  function handleMouseEnter(e, cellData) {
    const tooltip = tooltipRef.current
    if (!tooltip) return
    tooltip.style.display = 'block'
    tooltip.textContent = getTooltipText(cellData)
  }

  function handleMouseMove(e) {
    const tooltip = tooltipRef.current
    if (!tooltip) return
    let leftPos = e.clientX + 15, topPos = e.clientY + 15
    if (leftPos + 200 > window.innerWidth) leftPos = e.clientX - 210
    if (topPos + 150 > window.innerHeight) topPos = e.clientY - 160
    tooltip.style.left = leftPos + 'px'
    tooltip.style.top = topPos + 'px'
  }

  function handleMouseLeave() {
    if (tooltipRef.current) tooltipRef.current.style.display = 'none'
  }

  return (
    <>
      <div className="pitch-grid">
        {/* Headers */}
        <div></div>
        <div className="pitch-header-cell" style={{ gridColumn: '2 / span 2', borderBottom: '1px dashed rgba(255,255,255,0.1)' }}>OFF</div>
        <div className="pitch-header-cell" style={{ borderBottom: '1px dashed rgba(255,255,255,0.1)' }}><span className="pitch-header-stumps">|||</span></div>
        <div className="pitch-header-cell" style={{ gridColumn: '5 / span 2', borderBottom: '1px dashed rgba(255,255,255,0.1)' }}>LEG</div>

        {LENGTHS.map((len, r) => (
          <div key={len} style={{ display: 'contents' }}>
            <div className="pitch-label">{LENGTH_LABELS[r]}</div>
            {LINES.map((line) => {
              const cellData = map[len]?.[line]
              let bg = 'rgba(255,255,255,0.02)'
              let borderColor = 'rgba(255,255,255,0.05)'
              let content = ''

              if (cellData) {
                if (cellData.wickets > 0) {
                  const intensity = 0.4 + 0.6 * (cellData.wickets / maxWGradient)
                  bg = `rgba(249, 115, 22, ${intensity})`
                  borderColor = 'rgba(249, 115, 22, 0.4)'
                  content = cellData.wickets + 'W'
                } else if (cellData.runs > 0) {
                  const intensity = 0.1 + 0.3 * (cellData.runs / maxRGradient)
                  bg = `rgba(59, 130, 246, ${intensity})`
                  borderColor = 'rgba(59, 130, 246, 0.2)'
                }
              }

              return (
                <div
                  key={`${len}-${line}`}
                  className="pitch-cell"
                  style={{ background: bg, borderColor }}
                  onMouseEnter={(e) => handleMouseEnter(e, cellData)}
                  onMouseMove={handleMouseMove}
                  onMouseLeave={handleMouseLeave}
                >
                  {content}
                </div>
              )
            })}
          </div>
        ))}
      </div>
      <div
        ref={tooltipRef}
        style={{
          position: 'fixed', display: 'none', background: 'rgba(15, 23, 42, 0.95)',
          color: '#f8fafc', padding: '12px 16px', borderRadius: '8px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.1)', pointerEvents: 'none',
          zIndex: 9999, fontSize: '12px', fontFamily: 'Inter, sans-serif',
          whiteSpace: 'pre-wrap', lineHeight: '1.5',
        }}
      />
    </>
  )
}
