export default function LoadingOverlay({ visible = false, text = 'Fetching Analytics...' }) {
  if (!visible) return null
  return (
    <div id="loadingState" style={{ display: 'flex' }}>
      <span className="loader"></span>
      <p style={{ marginTop: '1rem', color: 'var(--text-secondary)', fontFamily: "'Outfit'" }}>{text}</p>
    </div>
  )
}
