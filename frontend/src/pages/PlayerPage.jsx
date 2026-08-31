import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAthleteProfile } from '../api/client'
import LoadingOverlay from '../components/LoadingOverlay'
import PlayerSearch from '../components/PlayerSearch'

export default function PlayerPage() {
  const { slug } = useParams()
  const [playerData, setPlayerData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!slug) return
    let active = true
    setLoading(true)
    setError(null)
    getAthleteProfile(slug).then(data => {
      if (active) setPlayerData(data)
    }).catch(err => {
      if (active) setError(err.message || 'Failed to load profile')
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [slug])

  if (!slug) {
    return (
      <div className="container">
        <div style={{ maxWidth: '600px', margin: '4rem auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>Find a Player</h2>
          <div style={{ position: 'relative' }}>
            <PlayerSearch 
              placeholder="Type a player name..." 
              onSelect={(p) => window.location.href = `/player/${p.id}`}
            />
          </div>
        </div>
      </div>
    )
  }

  if (loading) return <LoadingOverlay visible={true} text="Loading Player Profile..." />
  if (error) return <div style={{ color: '#ef4444', textAlign: 'center', padding: '2rem' }}>Error: {error}</div>
  if (!playerData || !playerData.athlete) return <div style={{ textAlign: 'center', padding: '2rem' }}>Player not found.</div>

  const { athlete, batting, bowling, favorites } = playerData

  return (
    <div className="container fade-in">
      {/* Profile Header */}
      <div className="profile-header">
        <img
          src={athlete.image_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(athlete.full_name)}&background=1e293b&color=fff`}
          alt={athlete.full_name}
          className="profile-img"
          onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(athlete.full_name)}&background=1e293b&color=fff` }}
        />
        <div className="profile-info">
          <h1>{athlete.full_name}</h1>
          <div className="profile-tags">
            <div className="tag"><i className="fas fa-flag"></i> {athlete.country_code || 'Unknown'}</div>
            {athlete.batting_style && <div className="tag"><i className="fas fa-baseball-bat-ball"></i> {athlete.batting_style}</div>}
            {athlete.bowling_style && <div className="tag"><i className="fas fa-baseball"></i> {athlete.bowling_style}</div>}
            {athlete.position && <div className="tag"><i className="fas fa-user-tag"></i> {athlete.position}</div>}
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <Link to={`/batter?id=${athlete.id}`} className="filter-btn" style={{ textDecoration: 'none', background: 'var(--accent-gradient)', color: 'white', border: 'none' }}>
              <i className="fas fa-baseball-bat-ball"></i> View Batter Analytics
            </Link>
            <Link to={`/bowler?id=${athlete.id}`} className="filter-btn" style={{ textDecoration: 'none', background: 'var(--surface-hover)', color: 'white' }}>
              <i className="fas fa-bolt"></i> View Bowler Analytics
            </Link>
          </div>
        </div>
      </div>

      {/* Batting Stats */}
      <h2 className="stats-section-title"><i className="fas fa-baseball-bat-ball"></i> Batting Statistics</h2>
      {batting && Object.keys(batting).length > 0 ? (
        <div className="format-grid">
          {Object.entries(batting).map(([fmt, stats]) => (
            <div className="format-card" key={fmt}>
              <h3>{fmt}</h3>
              <div className="stat-row"><span className="stat-label">Runs</span><span className="stat-value highlight">{Number(stats.runs).toLocaleString()}</span></div>
              <div className="stat-row"><span className="stat-label">Highest Score</span><span className="stat-value">{stats.hs}</span></div>
              <div className="stat-row"><span className="stat-label">Strike Rate</span><span className="stat-value">{stats.sr}</span></div>
              <div className="stat-row"><span className="stat-label">Balls Faced</span><span className="stat-value">{Number(stats.balls).toLocaleString()}</span></div>
              <div className="stat-row"><span className="stat-label">Sixes</span><span className="stat-value">{stats.sixes}</span></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">No batting data recorded for this player.</div>
      )}

      {/* Bowling Stats */}
      <h2 className="stats-section-title"><i className="fas fa-bolt"></i> Bowling Statistics</h2>
      {bowling && Object.keys(bowling).length > 0 ? (
        <div className="format-grid">
          {Object.entries(bowling).map(([fmt, stats]) => (
            <div className="format-card" key={fmt}>
              <h3>{fmt}</h3>
              <div className="stat-row"><span className="stat-label">Wickets</span><span className="stat-value highlight">{Number(stats.wickets).toLocaleString()}</span></div>
              <div className="stat-row"><span className="stat-label">Best Bowling</span><span className="stat-value">{stats.bb}</span></div>
              <div className="stat-row"><span className="stat-label">Economy</span><span className="stat-value">{stats.econ}</span></div>
              <div className="stat-row"><span className="stat-label">Overs</span><span className="stat-value">{stats.overs}</span></div>
              <div className="stat-row"><span className="stat-label">Runs Conceded</span><span className="stat-value">{Number(stats.runs).toLocaleString()}</span></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">No bowling data recorded for this player.</div>
      )}

      {/* Favorites */}
      {favorites && (
        <>
          <h2 className="stats-section-title" style={{ marginTop: '3rem' }}><i className="fas fa-star" style={{ color: '#fbbf24' }}></i> Player Favorites</h2>
          <div className="format-grid">
            <div className="format-card" style={{ borderTop: '4px solid #fbbf24' }}>
              <h3 style={{ color: '#fbbf24' }}>Batting Favorites</h3>
              <div className="stat-row">
                <span className="stat-label">Favorite Opponent</span>
                <span className="stat-value highlight" style={{ fontSize: '1.1rem', textAlign: 'right', maxWidth: '60%' }}>{favorites.batting_opponent?.name || 'N/A'}</span>
              </div>
              <div className="stat-row"><span className="stat-label">Most Runs Against</span><span className="stat-value">{favorites.batting_opponent?.total?.toLocaleString() || '0'}</span></div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '1rem 0' }} />
              <div className="stat-row">
                <span className="stat-label">Favorite Venue</span>
                <span className="stat-value highlight" style={{ fontSize: '1.1rem', textAlign: 'right', maxWidth: '60%' }}>{favorites.batting_venue?.name || 'N/A'}</span>
              </div>
              <div className="stat-row"><span className="stat-label">Most Runs At</span><span className="stat-value">{favorites.batting_venue?.total?.toLocaleString() || '0'}</span></div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '1rem 0' }} />
              <div className="stat-row">
                <span className="stat-label">Favorite Shot</span>
                <span className="stat-value highlight" style={{ fontSize: '1.1rem', textAlign: 'right', maxWidth: '60%' }}>{favorites.favorite_shot?.name || 'N/A'}</span>
              </div>
              <div className="stat-row"><span className="stat-label">Times Played</span><span className="stat-value">{favorites.favorite_shot?.total?.toLocaleString() || '0'}</span></div>
            </div>

            <div className="format-card" style={{ borderTop: '4px solid #38bdf8' }}>
              <h3 style={{ color: '#38bdf8' }}>Bowling Favorites</h3>
              <div className="stat-row">
                <span className="stat-label">Favorite Opponent</span>
                <span className="stat-value highlight" style={{ fontSize: '1.1rem', textAlign: 'right', maxWidth: '60%' }}>{favorites.bowling_opponent?.name || 'N/A'}</span>
              </div>
              <div className="stat-row"><span className="stat-label">Most Wickets Against</span><span className="stat-value">{favorites.bowling_opponent?.total?.toLocaleString() || '0'}</span></div>
              <hr style={{ border: 'none', borderTop: '1px solid var(--glass-border)', margin: '1rem 0' }} />
              <div className="stat-row">
                <span className="stat-label">Favorite Venue</span>
                <span className="stat-value highlight" style={{ fontSize: '1.1rem', textAlign: 'right', maxWidth: '60%' }}>{favorites.bowling_venue?.name || 'N/A'}</span>
              </div>
              <div className="stat-row"><span className="stat-label">Most Wickets At</span><span className="stat-value">{favorites.bowling_venue?.total?.toLocaleString() || '0'}</span></div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
