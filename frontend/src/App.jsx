import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BatterPage from './pages/BatterPage'
import BowlerPage from './pages/BowlerPage'
import FaceoffPage from './pages/FaceoffPage'
import PlayerPage from './pages/PlayerPage'
import PitchMapPage from './pages/PitchMapPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="batter" element={<BatterPage />} />
        <Route path="batter/:slug" element={<BatterPage />} />
        <Route path="bowler" element={<BowlerPage />} />
        <Route path="bowler/:slug" element={<BowlerPage />} />
        <Route path="faceoff" element={<FaceoffPage />} />
        <Route path="faceoff/:slug" element={<FaceoffPage />} />
        <Route path="player" element={<PlayerPage />} />
        <Route path="player/:slug" element={<PlayerPage />} />
        <Route path="pitchmap" element={<PitchMapPage />} />
      </Route>
    </Routes>
  )
}

