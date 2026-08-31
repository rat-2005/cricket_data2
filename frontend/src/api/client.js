const API_BASE = '';

async function apiFetch(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, options);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export function searchPlayers(q, opts = {}) {
  const params = new URLSearchParams({ q });
  if (opts.against_batter) params.set('against_batter', opts.against_batter);
  if (opts.against_bowler) params.set('against_bowler', opts.against_bowler);
  return apiFetch(`/api/search?${params}`);
}

export function getAthleteInfo(id) {
  return apiFetch(`/api/athlete/${id}`);
}

export function getFilters() {
  return apiFetch('/api/filters');
}

export function getBatterFilters(params) {
  return apiFetch(`/api/batter_filters?${new URLSearchParams(params)}`);
}

export async function getBatterStats(params) {
  const p = new URLSearchParams(params)
  const res = await fetch(`/api/stats/batter?${p.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch batter stats')
  return res.json()
}

export async function getBowlerFilters(params) {
  const p = new URLSearchParams(params)
  const res = await fetch(`/api/bowler_filters?${p.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch bowler filters')
  return res.json()
}

export async function getBowlerStats(params) {
  const p = new URLSearchParams(params)
  const res = await fetch(`/api/stats/bowler?${p.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch bowler stats')
  return res.json()
}

export async function getFaceoffFilters(params) {
  const p = new URLSearchParams(params)
  const res = await fetch(`/api/faceoff_filters?${p.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch faceoff filters')
  return res.json()
}

export async function getFaceoffStats(params) {
  const p = new URLSearchParams(params)
  const res = await fetch(`/api/stats/faceoff?${p.toString()}`)
  if (!res.ok) throw new Error('Failed to fetch faceoff stats')
  return res.json()
}

export async function getAthleteProfile(idOrSlug) {
  const res = await fetch(`/api/player/${encodeURIComponent(idOrSlug)}`)
  if (!res.ok) throw new Error('Failed to fetch player profile')
  return res.json()
}

export function getPlayerProfile(identifier) {
  return apiFetch(`/api/athlete/${identifier}`);
}
