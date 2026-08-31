import { Outlet, NavLink } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="container fade-in">
      <header>
        <div className="logo">
          <NavLink to="/" style={{ textDecoration: 'none' }}>
            <h1>Cricket Analytics</h1>
          </NavLink>
        </div>
        <div className="nav-links">
          <NavLink to="/batter" className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-baseball-bat-ball"></i> Batter
          </NavLink>
          <NavLink to="/bowler" className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-bolt"></i> Bowler
          </NavLink>
          <NavLink to="/faceoff" className={({ isActive }) => isActive ? 'active' : ''}>
            <i className="fas fa-people-arrows"></i> Face-off
          </NavLink>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
