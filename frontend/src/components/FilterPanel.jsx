import { useState, useEffect, useRef, useCallback } from 'react'
import CustomMultiSelect from './CustomMultiSelect'

const FILTER_KEYS = [
  'format', 'league', 'year', 'phase', 'venue', 'opponent',
  'bowling_type', 'batting_type', 'innings', 'result', 'recent',
  'wicket_type', 'pitch_length', 'pitch_line', 'shot_type', 'delivery_output'
]

const STATIC_OPTIONS = {
  phase: [
    { value: 'Powerplay', label: 'Powerplay (1-6)' },
    { value: 'Middle', label: 'Middle Overs (7-15)' },
    { value: 'Death', label: 'Death Overs (16-20)' },
  ],
  innings: [
    { value: '1', label: '1st Innings' },
    { value: '2', label: '2nd Innings' },
    { value: '3', label: '3rd Innings' },
    { value: '4', label: '4th Innings' },
  ],
  result: [
    { value: 'Won', label: 'Won' },
    { value: 'Lost', label: 'Lost' },
  ],
  recent: [
    { value: '5', label: 'Last 5 Matches' },
    { value: '10', label: 'Last 10 Matches' },
    { value: '20', label: 'Last 20 Matches' },
  ],
  delivery_output: [
    { value: '0', label: '0 Runs' },
    { value: '1', label: '1 Run' },
    { value: '2', label: '2 Runs' },
    { value: '3', label: '3 Runs' },
    { value: '4', label: '4 Runs' },
    { value: '5', label: '5 Runs' },
    { value: '6', label: '6 Runs' },
    { value: '7+', label: '7+ Runs' },
    { value: 'Wicket', label: 'Wicket' },
    { value: 'Wide', label: 'Wide' },
  ],
}

const FILTER_LABELS = {
  format: 'Format',
  league: 'League',
  year: 'Year',
  phase: 'Phase',
  venue: 'Venue',
  opponent: 'Opponent',
  bowling_type: 'Bowling Type',
  batting_type: 'Batting Type',
  innings: 'Innings',
  result: 'Match Result',
  recent: 'Recent Matches',
  wicket_type: 'Wicket Type',
  pitch_length: 'Pitch Length',
  pitch_line: 'Pitch Line',
  shot_type: 'Shot Type',
  delivery_output: 'Delivery Output',
}

const ALL_LABELS = {
  format: 'All Formats',
  league: 'All Leagues',
  year: 'All Years',
  phase: 'All Phases',
  venue: 'All Venues',
  opponent: 'All Opponents',
  bowling_type: 'All Types',
  batting_type: 'All Types',
  innings: 'All Innings',
  result: 'All Results',
  recent: 'All Matches',
  wicket_type: 'All Types',
  pitch_length: 'All Lengths',
  pitch_line: 'All Lines',
  shot_type: 'All Shots',
  delivery_output: 'All Outputs',
}

export default function FilterPanel({
  visibleFilters = [],
  filterOptions = {},
  values = {},
  negations = {},
  cascaded = true,
  onCascadeToggle,
  onFilterChange,
  onNegationToggle,
  onReset,
  onAnalyze,
}) {
  function getOptions(key) {
    if (STATIC_OPTIONS[key] && !filterOptions[key]) return STATIC_OPTIONS[key]
    const opts = filterOptions[key] || []
    return opts.map((o) => (typeof o === 'object' ? o : { value: o, label: o }))
  }

  function handleChange(key, selected) {
    if (onFilterChange) onFilterChange(key, selected)
  }

  function handleNot(key) {
    if (onNegationToggle) onNegationToggle(key)
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%', marginBottom: '1rem', position: 'relative', zIndex: 100 }}>
        <label
          style={{
            display: 'flex', alignItems: 'center', gap: '0.6rem', color: 'white',
            background: 'rgba(255, 255, 255, 0.05)', padding: '0.6rem 1.2rem',
            borderRadius: '30px', border: '1px solid rgba(255, 255, 255, 0.1)',
            fontFamily: "'Inter', sans-serif", fontSize: '0.95rem', cursor: 'pointer',
            backdropFilter: 'blur(10px)', transition: 'all 0.3s',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
          }}
          title="When ON, selecting a filter narrows down the other options. When OFF, all options are always visible."
        >
          <input
            type="checkbox"
            checked={cascaded}
            onChange={(e) => onCascadeToggle && onCascadeToggle(e.target.checked)}
            style={{ accentColor: 'var(--accent-blue)', width: '1.1rem', height: '1.1rem', cursor: 'pointer' }}
          />
          <i className="fas fa-filter" style={{ color: 'var(--accent-blue)' }}></i>
          <strong>Cascaded Filters</strong>
        </label>
      </div>

      <div className="glass-panel" style={{ display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end', position: 'relative', zIndex: 50 }}>
        {visibleFilters.map((key) => (
          <div key={key} style={{ flex: 1, minWidth: '150px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>
                {FILTER_LABELS[key] || key}
              </label>
              <button
                type="button"
                className={`filter-btn ${negations[key] ? 'active-not' : ''}`}
                onClick={() => handleNot(key)}
                title="Exclude selected"
              >
                Not
              </button>
            </div>
            <CustomMultiSelect
              options={getOptions(key)}
              selected={values[key] || []}
              allLabel={ALL_LABELS[key] || 'All'}
              negated={negations[key] || false}
              onChange={(sel) => handleChange(key, sel)}
            />
          </div>
        ))}

        <div style={{ flex: '0 0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
          <button
            type="button"
            onClick={onReset}
            style={{
              padding: '0.8rem 2rem', borderRadius: '12px', border: '1px solid var(--glass-border)',
              background: 'rgba(0,0,0,0.4)', color: 'white', fontFamily: "'Outfit', sans-serif",
              fontWeight: 600, fontSize: '1.1rem', cursor: 'pointer', transition: 'background 0.2s',
            }}
          >
            Reset Options
          </button>
          <button
            onClick={onAnalyze}
            style={{
              padding: '0.8rem 2rem', borderRadius: '12px', border: 'none',
              background: 'var(--accent-gradient)', color: 'white', fontFamily: "'Outfit'",
              fontWeight: 600, fontSize: '1.1rem', cursor: 'pointer', boxShadow: 'var(--neon-glow)',
              transition: 'transform 0.2s',
            }}
          >
            Analyze
          </button>
        </div>
      </div>
    </>
  )
}

/**
 * Build URLSearchParams from filter values and negations.
 */
export function buildFilterParams(values, negations, extraParams = {}) {
  const params = { ...extraParams }
  for (const key of FILTER_KEYS) {
    const val = values[key]
    if (val && val.length > 0) {
      params[key] = val.join(',')
    } else {
      params[key] = 'All'
    }
    params[`${key}_not`] = negations[key] ? 'true' : 'false'
  }
  return params
}
