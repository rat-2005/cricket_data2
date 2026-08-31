import { useState, useEffect, useRef } from 'react'

export default function CustomMultiSelect({ options = [], selected = [], allLabel = 'All', negated = false, onChange }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const wrapperRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const allOptions = [{ value: 'All', label: allLabel }, ...options]
  const isAll = selected.length === 0

  const filteredOptions = allOptions.filter((o) => {
    if (!search) return true
    return o.label.toLowerCase().includes(search.toLowerCase()) || o.value.toLowerCase().includes(search.toLowerCase())
  })

  function toggleOption(value) {
    if (value === 'All') {
      onChange([])
      return
    }
    let next
    if (selected.includes(value)) {
      next = selected.filter((v) => v !== value)
    } else {
      next = [...selected, value]
    }
    onChange(next)
  }

  function selectAllMatching(checked) {
    if (checked) {
      const matchingValues = filteredOptions.filter((o) => o.value !== 'All').map((o) => o.value)
      const merged = [...new Set([...selected, ...matchingValues])]
      onChange(merged)
    } else {
      const matchingValues = new Set(filteredOptions.filter((o) => o.value !== 'All').map((o) => o.value))
      onChange(selected.filter((v) => !matchingValues.has(v)))
    }
  }

  const headerText = isAll
    ? allLabel
    : selected.map((v) => {
        const opt = options.find((o) => o.value === v)
        const label = opt ? opt.label : v
        return negated ? `Not ${label}` : label
      }).join(', ')

  const visibleNonAll = filteredOptions.filter((o) => o.value !== 'All')
  const allVisibleChecked = visibleNonAll.length > 0 && visibleNonAll.every((o) => selected.includes(o.value))

  return (
    <div ref={wrapperRef} className="custom-multi-wrapper">
      <div className="custom-multi-header" onClick={() => setOpen(!open)}>
        <span>{headerText}</span>
        <i className="fas fa-chevron-down"></i>
      </div>

      {open && (
        <div className="custom-multi-dropdown active">
          <div className="custom-multi-search-wrapper">
            <input
              type="text"
              className="custom-multi-search-input"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
            <label className="custom-multi-select-all">
              <input
                type="checkbox"
                checked={allVisibleChecked}
                onChange={(e) => selectAllMatching(e.target.checked)}
              />
              <span>Select Matching</span>
            </label>
          </div>

          <div className="custom-multi-options">
            {filteredOptions.map((o) => {
              const checked = o.value === 'All' ? isAll : selected.includes(o.value)
              return (
                <label key={o.value} className="custom-multi-option">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleOption(o.value)}
                    value={o.value}
                  />
                  <span>{negated && o.value !== 'All' ? `Not ${o.label}` : o.label}</span>
                </label>
              )
            })}
          </div>

          <div className="custom-multi-footer">
            <button className="custom-multi-btn" onClick={() => setOpen(false)}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
