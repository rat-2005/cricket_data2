import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <main className="hero">
      <h1>The Deep Data<br />Engine</h1>
      <p>Accessing 24 million deliveries across ESPN, Cricsheet, and ICC to visualize Wagon Wheels, Shot Masteries, and Pitching Heatmaps in real-time.</p>

      <div className="portal-grid">
        <Link to="/batter" className="portal-card">
          <i className="fas fa-baseball-bat-ball portal-icon"></i>
          <h2>Batter Analytics</h2>
          <p>Wagon Wheels & Shot Mastery</p>
        </Link>

        <Link to="/faceoff" className="portal-card">
          <i className="fas fa-people-arrows portal-icon"></i>
          <h2>Head-to-Head</h2>
          <p>Ultimate Matchup Simulator</p>
        </Link>

        <Link to="/bowler" className="portal-card">
          <i className="fas fa-bolt portal-icon"></i>
          <h2>Bowler Analytics</h2>
          <p>Heatmaps & Pace Profiles</p>
        </Link>
      </div>

      <div className="db-stat">
        <i className="fas fa-database"></i> 24,198,402 Deliveries Indexed
      </div>
    </main>
  )
}
