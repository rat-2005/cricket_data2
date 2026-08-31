import { useState, useEffect, useRef } from 'react'
import { searchPlayers } from '../api/client'

export default function PlayerSearch({ onSelect, placeholder = 'Search player...', initialValue = '' }) {
  const [query, setQuery] = useState(initialValue)
  const [results, setResults] = useState([])
  const [showResults, setShowResults] = useState(false)
  const [loading, setLoading] = useState(false)
  const timeoutRef = useRef(null)
  const wrapperRef = useRef(null)

  useEffect(() => {
    setQuery(initialValue)
  }, [initialValue])

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowResults(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  function handleInput(e) {
    const val = e.target.value
    setQuery(val)
    clearTimeout(timeoutRef.current)

    if (val.trim().length < 1) {
      setShowResults(false)
      setResults([])
      return
    }

    setLoading(true)
    setShowResults(true)

    timeoutRef.current = setTimeout(async () => {
      try {
        const data = await searchPlayers(val.trim())
        setResults(data)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
  }

  function handleSelect(player) {
    setQuery(player.full_name)
    setShowResults(false)
    if (onSelect) onSelect(player)
  }

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <input
        type="text"
        value={query}
        onChange={handleInput}
        placeholder={placeholder}
        autoComplete="off"
        style={{
          width: '100%',
          padding: '0.8rem 1rem',
          background: 'rgba(0, 0, 0, 0.4)',
          border: '1px solid var(--glass-border)',
          borderRadius: '12px',
          color: 'var(--text-primary)',
          fontFamily: "'Inter', sans-serif",
          fontSize: '0.95rem',
        }}
      />
      {showResults && (
        <div className="search-results active">
          {loading ? (
            <div style={{ padding: '1rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
              <i className="fas fa-spinner fa-spin"></i>
            </div>
          ) : results.length > 0 ? (
            results.map((p) => (
              <div
                key={p.id}
                className="search-result-item"
                onClick={() => handleSelect(p)}
              >
                <div style={{ fontWeight: 600, fontFamily: "'Outfit'", color: 'white' }}>
                  {p.full_name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {p.primary_team || p.country_code || ''}
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No players found
            </div>
          )}
        </div>
      )}
    </div>
  )
}
