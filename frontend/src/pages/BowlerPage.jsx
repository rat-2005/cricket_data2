import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import PlayerSearch from '../components/PlayerSearch'
import FilterPanel, { buildFilterParams } from '../components/FilterPanel'
import LoadingOverlay from '../components/LoadingOverlay'
import PitchHeatmap from '../components/charts/PitchHeatmap'
import DismissalChart from '../components/charts/DismissalChart'
import { getAthleteInfo, getFilters, getBowlerFilters, getBowlerStats } from '../api/client'

const BOWLER_FILTERS = [
  'format', 'league', 'year', 'phase', 'venue', 'opponent',
  'batting_type', 'innings', 'result', 'recent',
  'wicket_type', 'pitch_length', 'pitch_line', 'shot_type', 'delivery_output',
]

export default function BowlerPage() {
  const { slug } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()

  const [athleteId, setAthleteId] = useState(searchParams.get('id') || '')
  const [athleteName, setAthleteName] = useState('?')
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
        }))
      } catch (e) { console.error('Failed to load filters', e) }

      let id = searchParams.get('id') || ''
      if (slug) {
        try {
          const info = await getAthleteInfo(slug)
          if (info?.id) { id = info.id; setAthleteName(info.full_name) }
        } catch {}
      }

      if (id) {
        setAthleteId(id)
        if (!slug) {
          try { const info = await getAthleteInfo(id); if (info) setAthleteName(info.full_name) } catch {}
        }
        fetchCascadedFilters(id)
      }
    }
    init()
  }, [slug])

  const fetchCascadedFilters = useCallback(async (id, sourceKey = null) => {
    if (!id) return
    setLoading(true)
    try {
      const params = cascaded
        ? buildFilterParams(filterValues, negations, { id })
        : { id }
      const filters = await getBowlerFilters(params)

      setFilterOptions((prev) => {
        const next = { ...prev }
        if (sourceKey !== 'format' && filters.formats) next.format = filters.formats
        if (sourceKey !== 'league' && filters.leagues) next.league = filters.leagues
        if (sourceKey !== 'venue' && filters.venues) next.venue = filters.venues
        if (sourceKey !== 'opponent' && filters.opponents) next.opponent = filters.opponents
        if (sourceKey !== 'batting_type' && filters.batting_types) next.batting_type = filters.batting_types
        if (sourceKey !== 'year' && filters.years) next.year = filters.years
        if (sourceKey !== 'innings' && filters.innings) next.innings = filters.innings?.map((i) => ({ value: String(i), label: `Innings ${i}` }))
        if (sourceKey !== 'result' && filters.results) next.result = filters.results?.map((r) => ({ value: r, label: r }))
        if (sourceKey !== 'wicket_type' && filters.wicket_types) next.wicket_type = filters.wicket_types
        if (sourceKey !== 'pitch_length' && filters.pitch_lengths) next.pitch_length = filters.pitch_lengths
        if (sourceKey !== 'pitch_line' && filters.pitch_lines) next.pitch_line = filters.pitch_lines
        if (sourceKey !== 'shot_type' && filters.shot_types) next.shot_type = filters.shot_types
        if (sourceKey !== 'phase' && filters.phases) next.phase = filters.phases?.map((p) => ({ value: p, label: p }))
        return next
      })
    } catch (e) { console.error('Filter fetch failed', e) }
    setLoading(false)
  }, [cascaded, filterValues, negations])

  function handlePlayerSelect(player) {
    setAthleteId(player.id)
    setAthleteName(player.full_name)
    setSearchParams({ id: player.id })
    setShowEmpty(true)
    setStats(null)
    fetchCascadedFilters(player.id)
  }

  function handleFilterChange(key, selected) {
    setFilterValues((prev) => ({ ...prev, [key]: selected }))
    if (cascaded && athleteId) setTimeout(() => fetchCascadedFilters(athleteId, key), 0)
  }

  function handleNegationToggle(key) {
    setNegations((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  function handleReset() {
    setFilterValues({})
    setNegations({})
    if (athleteId) fetchCascadedFilters(athleteId)
  }

  async function handleAnalyze() {
    if (!athleteId) return
    setShowEmpty(false)
    setLoading(true)
    try {
      const params = buildFilterParams(filterValues, negations, { id: athleteId })
      const data = await getBowlerStats(params)
      setStats(data)
    } catch (e) {
      console.error(e)
      setStats(null)
    }
    setLoading(false)
  }

  return (
    <div className="dashboard">
      <div className="glass-panel" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end', position: 'relative', zIndex: 1005, marginBottom: '1rem' }}>
        <div style={{ flex: 1, minWidth: 250, position: 'relative', zIndex: 1000 }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem', display: 'block', fontWeight: 600, textTransform: 'uppercase' }}>
            <i className="fas fa-user"></i> Select Bowler
          </label>
          <PlayerSearch placeholder="Search bowler..." onSelect={handlePlayerSelect} initialValue={athleteName !== '?' ? athleteName : ''} />
        </div>
      </div>

      <FilterPanel
        visibleFilters={BOWLER_FILTERS}
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
          <div className="glass-panel" style={{ display: 'inline-block', padding: '1.5rem 4rem' }}>
            <Link to={`/player/${athleteId}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <h2 className="player-name" style={{ marginBottom: 0 }}>{athleteName}</h2>
              <div style={{ fontSize: '0.85rem', color: 'var(--accent-blue)', marginBottom: '0.5rem' }}>
                <i className="fas fa-external-link-alt"></i> View Full Profile
              </div>
            </Link>
            <div style={{ color: 'var(--text-secondary)', fontFamily: "'Outfit'" }}>Career Bowling Overview</div>
          </div>
        </div>

        {stats && (
          <div>
            <div className="bento-grid">
              <div className="glass-panel stat-box">
                <div className="stat-label">Wickets</div>
                <div className="stat-value" style={{ color: 'var(--accent-blue)', background: 'none', WebkitTextFillColor: 'var(--accent-blue)' }}>{stats.wickets}</div>
              </div>
              <div className="glass-panel stat-box">
                <div className="stat-label">Economy</div>
                <div className="stat-value small">{stats.eco}</div>
                <div className="stat-subtext">Runs/Over</div>
              </div>
              <div className="glass-panel stat-box">
                <div className="stat-label">Average</div>
                <div className="stat-value small">{stats.avg}</div>
                <div className="stat-subtext">Runs/Wicket</div>
              </div>
              <div className="glass-panel stat-box">
                <div className="stat-label">Best Bowling</div>
                <div className="stat-value" style={{ fontSize: '2rem' }}>{stats.best}</div>
              </div>
            </div>

            <div className="bento-grid" style={{ marginTop: '1.5rem' }}>
              <div className="glass-panel span-4 chart-container" style={{ minHeight: 400, padding: '1.5rem' }}>
                <div className="chart-header">
                  <h3 className="chart-title"><i className="fas fa-fire" style={{ color: '#f97316' }}></i> Pitch Heatmap</h3>
                </div>
                <div className="chart-wrapper" style={{ display: 'flex', justifyContent: 'center', padding: '1rem 0', overflowX: 'auto' }}>
                  <PitchHeatmap data={stats.pitch_heatmap || []} />
                </div>
              </div>

              <div className="glass-panel span-2 chart-container" style={{ minHeight: 350 }}>
                <div className="chart-header">
                  <h3 className="chart-title"><i className="fas fa-skull" style={{ color: 'var(--accent-blue)' }}></i> Dismissal Methods</h3>
                </div>
                <div className="chart-wrapper">
                  <DismissalChart wicketData={stats.wicket_data || {}} />
                </div>
              </div>
            </div>
          </div>
        )}

        {showEmpty && !stats && (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
            <i className="fas fa-search" style={{ fontSize: '4rem', opacity: 0.3, marginBottom: '1.5rem' }}></i>
            <h3 style={{ fontFamily: "'Outfit'", color: 'white' }}>Awaiting Selection</h3>
            <p>Search and select a bowler to view their deep analytics.</p>
          </div>
        )}
      </div>

      <LoadingOverlay visible={loading} />
    </div>
  )
}
