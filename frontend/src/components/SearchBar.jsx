import { useState } from 'react'

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch(query)
  }

  return (
    <div className="search-container">
      <form onSubmit={handleSubmit} className="search-bar">
        <input
          type="text"
          placeholder="Search for products..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>
    </div>
  )
}

export default SearchBar
