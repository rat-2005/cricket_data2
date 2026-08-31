import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import PlayerSearch from '../components/PlayerSearch'
import FilterPanel, { buildFilterParams } from '../components/FilterPanel'
import LoadingOverlay from '../components/LoadingOverlay'
import WagonWheel from '../components/charts/WagonWheel'
import PitchHeatmap from '../components/charts/PitchHeatmap'
import { getAthleteInfo, getFilters, getFaceoffFilters, getFaceoffStats } from '../api/client'

const FACEOFF_FILTERS = [
  'format', 'league', 'year', 'phase', 'venue',
  'innings', 'result', 'recent',
  'wicket_type', 'pitch_length', 'pitch_line', 'shot_type', 'delivery_output'
]

export default function FaceoffPage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const [batterId, setBatterId] = useState(searchParams.get('batter') || '')
  const [batterName, setBatterName] = useState('?')
  const [bowlerId, setBowlerId] = useState(searchParams.get('bowler') || '')
  const [bowlerName, setBowlerName] = useState('?')

  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [showEmpty, setShowEmpty] = useState(true)

  const [filterOptions, setFilterOptions] = useState({})
  const [filterValues, setFilterValues] = useState({})
  const [negations, setNegations] = useState({})
  const [cascaded, setCascaded] = useState(true)

  useEffect(() => {
    async function init() {
      try {
        const filters = await getFilters()
        setFilterOptions((prev) => ({
          ...prev,
          format: filters.formats || [],
          league: filters.leagues || [],
          venue: filters.venues || [],
          batting_type: filters.batting_types || [],
          bowling_type: filters.bowling_types || [],
        }))
      } catch (e) { console.error('Failed to load global filters', e) }

      const bId = searchParams.get('batter')
      const boId = searchParams.get('bowler')
      if (bId) {
        getAthleteInfo(bId).then(info => { if (info) setBatterName(info.full_name) }).catch(() => {})
      }
      if (boId) {
        getAthleteInfo(boId).then(info => { if (info) setBowlerName(info.full_name) }).catch(() => {})
      }
      if (bId && boId) {
        fetchCascadedFilters(bId, boId)
      }
    }
    init()
  }, [])

  const fetchCascadedFilters = useCallback(async (bId, boId, sourceKey = null) => {
    if (!bId && !boId) return
    setLoading(true)
    try {
      const baseParams = { batter_id: bId, bowler_id: boId }
      const params = cascaded ? buildFilterParams(filterValues, negations, baseParams) : baseParams
      const filters = await getFaceoffFilters(params)

      setFilterOptions((prev) => {
        const next = { ...prev }
        if (sourceKey !== 'format' && filters.formats) next.format = filters.formats
        if (sourceKey !== 'league' && filters.leagues) next.league = filters.leagues
        if (sourceKey !== 'venue' && filters.venues) next.venue = filters.venues
        if (sourceKey !== 'year' && filters.years) next.year = filters.years
        if (sourceKey !== 'innings' && filters.innings) next.innings = filters.innings?.map(i => ({ value: String(i), label: `Innings ${i}` }))
        if (sourceKey !== 'result' && filters.results) next.result = filters.results?.map(r => ({ value: r, label: r }))
        if (sourceKey !== 'wicket_type' && filters.wicket_types) next.wicket_type = filters.wicket_types
        if (sourceKey !== 'pitch_length' && filters.pitch_lengths) next.pitch_length = filters.pitch_lengths
        if (sourceKey !== 'pitch_line' && filters.pitch_lines) next.pitch_line = filters.pitch_lines
        if (sourceKey !== 'shot_type' && filters.shot_types) next.shot_type = filters.shot_types
        if (sourceKey !== 'phase' && filters.phases) next.phase = filters.phases?.map(p => ({ value: p, label: p }))
        return next
      })
    } catch (e) { console.error('Faceoff filter fetch failed', e) }
    setLoading(false)
  }, [cascaded, filterValues, negations])

  function handleBatterSelect(player) {
    setBatterId(player.id)
    setBatterName(player.full_name)
    updateSearchParams(player.id, bowlerId)
    if (player.id && bowlerId) fetchCascadedFilters(player.id, bowlerId)
  }

  function handleBowlerSelect(player) {
    setBowlerId(player.id)
    setBowlerName(player.full_name)
    updateSearchParams(batterId, player.id)
    if (batterId && player.id) fetchCascadedFilters(batterId, player.id)
  }

  function updateSearchParams(bId, boId) {
    const p = new URLSearchParams()
    if (bId) p.set('batter', bId)
    if (boId) p.set('bowler', boId)
    setSearchParams(p)
    setShowEmpty(true)
    setStats(null)
  }

  function handleFilterChange(key, selected) {
    setFilterValues(prev => ({ ...prev, [key]: selected }))
    if (cascaded && batterId && bowlerId) setTimeout(() => fetchCascadedFilters(batterId, bowlerId, key), 0)
  }

  function handleNegationToggle(key) {
    setNegations(prev => ({ ...prev, [key]: !prev[key] }))
  }

  function handleReset() {
    setFilterValues({})
    setNegations({})
    if (batterId && bowlerId) fetchCascadedFilters(batterId, bowlerId)
  }

  async function handleAnalyze() {
    if (!batterId || !bowlerId) return
    setShowEmpty(false)
    setLoading(true)
    try {
      const params = buildFilterParams(filterValues, negations, { batter_id: batterId, bowler_id: bowlerId })
      const data = await getFaceoffStats(params)
      setStats(data)
    } catch (e) {
      console.error(e)
      setStats(null)
    }
    setLoading(false)
  }

  return (
    <div className="dashboard">
      {/* Dual Player Search */}
      <div className="glass-panel" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end', position: 'relative', zIndex: 1005, marginBottom: '1rem' }}>
        <div style={{ flex: 1, minWidth: 250, position: 'relative', zIndex: 1001 }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem', display: 'block', fontWeight: 600, textTransform: 'uppercase' }}>
            <i className="fas fa-user"></i> Batter
          </label>
          <PlayerSearch placeholder="Search batter..." onSelect={handleBatterSelect} initialValue={batterName !== '?' ? batterName : ''} />
        </div>
        <div style={{ flex: 1, minWidth: 250, position: 'relative', zIndex: 1000 }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem', display: 'block', fontWeight: 600, textTransform: 'uppercase' }}>
            <i className="fas fa-user"></i> Bowler
          </label>
          <PlayerSearch placeholder="Search bowler..." onSelect={handleBowlerSelect} initialValue={bowlerName !== '?' ? bowlerName : ''} />
        </div>
      </div>

      <FilterPanel
        visibleFilters={FACEOFF_FILTERS}
        filterOptions={filterOptions}
        values={filterValues}
        negations={negations}
        cascaded={cascaded}
        onCascadeToggle={setCascaded}
        onFilterChange={handleFilterChange}
        onNegationToggle={handleNegationToggle}
        onReset={handleReset}
        onAnalyze={handleAnalyze}
      />

      <div>
        <div className="player-header">
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
            <div className="glass-panel" style={{ flex: 1, minWidth: 200, padding: '1.5rem' }}>
              <div className="stat-label">Batter</div>
              {batterId ? (
                <Link to={`/player/${batterId}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
                  <h2 className="player-name" style={{ marginBottom: 0 }}>{batterName}</h2>
                  <div style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem' }}><i className="fas fa-external-link-alt"></i> View Profile</div>
                </Link>
              ) : (
                <h2 className="player-name" style={{ marginBottom: 0 }}>?</h2>
              )}
            </div>
            <div className="vs-badge" style={{
              background: 'var(--accent-gradient)', color: 'white', fontWeight: 800, fontSize: '1.5rem',
              width: '60px', height: '60px', borderRadius: '50%', display: 'flex', alignItems: 'center',
              justifyContent: 'center', boxShadow: 'var(--neon-glow)', border: '4px solid var(--bg-color)'
            }}>VS</div>
            <div className="glass-panel" style={{ flex: 1, minWidth: 200, padding: '1.5rem' }}>
              <div className="stat-label">Bowler</div>
              {bowlerId ? (
                <Link to={`/player/${bowlerId}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
                  <h2 className="player-name" style={{ marginBottom: 0 }}>{bowlerName}</h2>
                  <div style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem' }}><i className="fas fa-external-link-alt"></i> View Profile</div>
                </Link>
              ) : (
                <h2 className="player-name" style={{ marginBottom: 0 }}>?</h2>
              )}
            </div>
          </div>
        </div>

        {stats && (
          <div className="bento-grid" style={{ marginTop: '1.5rem' }}>
            <div className="glass-panel span-2 chart-container" style={{ minHeight: 350 }}>
              <div className="chart-header">
                <h3 className="chart-title"><i className="fas fa-th" style={{ color: 'var(--accent-blue)' }}></i> Pitch Map (Runs & Wickets)</h3>
              </div>
              <div className="chart-wrapper" style={{ display: 'flex', justifyContent: 'center', padding: '1rem 0', overflowX: 'auto' }}>
                <PitchHeatmap data={stats.pitch_heatmap || []} />
              </div>
            </div>

            <div className="glass-panel span-2 chart-container" style={{ minHeight: 350, overflowY: 'auto' }}>
              <div className="chart-header">
                <h3 className="chart-title"><i className="fas fa-history" style={{ color: '#a855f7' }}></i> Recent Encounters</h3>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem', fontFamily: "'Inter', sans-serif", fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Date</th>
                    <th style={{ padding: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Performance</th>
                    <th style={{ padding: '0.8rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {(stats.recent_encounters || []).length > 0 ? (
                    stats.recent_encounters.map((m, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '0.8rem', color: '#cbd5e1' }}>{m.date}<div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{m.format}</div></td>
                        <td style={{ padding: '0.8rem', fontWeight: 600 }}>{m.runs} off {m.balls} <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>({m.sr})</span></td>
                        <td style={{ padding: '0.8rem' }}>
                          {m.dismissed ? <span style={{ color: '#ef4444', fontWeight: 600 }}>Out</span> : <span style={{ color: '#10b981', fontWeight: 600 }}>Not Out</span>}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan="3" style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No recent encounters found</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="glass-panel span-2 chart-container" style={{ minHeight: 350 }}>
              <div className="chart-header">
                <h3 className="chart-title"><i className="fas fa-life-ring" style={{ color: 'var(--accent-blue)' }}></i> Head-to-Head Wagon Wheel</h3>
              </div>
              <div className="chart-wrapper" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <WagonWheel data={stats.wagon_wheel || []} />
              </div>
            </div>
          </div>
        )}

        {showEmpty && !stats && (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
            <i className="fas fa-search" style={{ fontSize: '4rem', opacity: 0.3, marginBottom: '1.5rem' }}></i>
            <h3 style={{ fontFamily: "'Outfit'", color: 'white' }}>Awaiting Selection</h3>
            <p>Search and select both a batter and a bowler to view their head-to-head records.</p>
          </div>
        )}
      </div>

      <LoadingOverlay visible={loading} />
    </div>
  )
}
