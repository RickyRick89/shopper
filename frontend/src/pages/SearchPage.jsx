import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { apiService } from '../services/api'

function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Search filters
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [category, setCategory] = useState(searchParams.get('category') || '')
  const [brand, setBrand] = useState(searchParams.get('brand') || '')
  const [minPrice, setMinPrice] = useState(searchParams.get('min_price') || '')
  const [maxPrice, setMaxPrice] = useState(searchParams.get('max_price') || '')
  const [zipCode, setZipCode] = useState(searchParams.get('zip') || '')
  const [radius, setRadius] = useState(searchParams.get('radius') || '25')
  const [inStock, setInStock] = useState(searchParams.get('in_stock') === 'true')
  
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Fetch search suggestions
  const fetchSuggestions = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setSuggestions([])
      return
    }
    try {
      const data = await apiService.getSearchSuggestions(searchQuery)
      setSuggestions(data)
    } catch {
      setSuggestions([])
    }
  }

  // Perform search
  const performSearch = async () => {
    setLoading(true)
    setError(null)
    setShowSuggestions(false)

    try {
      const params = {}
      if (query) params.q = query
      if (category) params.category = category
      if (brand) params.brand = brand
      if (minPrice) params.min_price = parseFloat(minPrice)
      if (maxPrice) params.max_price = parseFloat(maxPrice)
      if (zipCode) params.zip_code = zipCode
      if (radius) params.radius = parseFloat(radius)
      if (inStock) params.in_stock = true

      const data = await apiService.searchProducts(params)
      setProducts(data)

      // Update URL params
      const newParams = new URLSearchParams()
      if (query) newParams.set('q', query)
      if (category) newParams.set('category', category)
      if (brand) newParams.set('brand', brand)
      if (minPrice) newParams.set('min_price', minPrice)
      if (maxPrice) newParams.set('max_price', maxPrice)
      if (zipCode) newParams.set('zip', zipCode)
      if (radius && radius !== '25') newParams.set('radius', radius)
      if (inStock) newParams.set('in_stock', 'true')
      setSearchParams(newParams)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Initial search on mount if there are params
  useEffect(() => {
    if (searchParams.toString()) {
      performSearch()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleQueryChange = (e) => {
    const value = e.target.value
    setQuery(value)
    fetchSuggestions(value)
    setShowSuggestions(true)
  }

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    setSuggestions([])
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    performSearch()
  }

  const handleReset = () => {
    setQuery('')
    setCategory('')
    setBrand('')
    setMinPrice('')
    setMaxPrice('')
    setZipCode('')
    setRadius('25')
    setInStock(false)
    setProducts([])
    setSearchParams(new URLSearchParams())
  }

  return (
    <div className="search-page">
      <h1 className="page-title">Advanced Search</h1>
      
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-main">
          <div className="search-input-wrapper">
            <input
              type="text"
              placeholder="Search for products..."
              value={query}
              onChange={handleQueryChange}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              className="search-input"
            />
            {showSuggestions && suggestions.length > 0 && (
              <ul className="suggestions-list">
                {suggestions.map((suggestion, index) => (
                  <li 
                    key={index} 
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="suggestion-item"
                  >
                    {suggestion}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="filter-section">
          <h3>Filters</h3>
          
          <div className="filter-grid">
            <div className="filter-group">
              <label htmlFor="category">Category</label>
              <input
                id="category"
                type="text"
                placeholder="e.g., Electronics"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label htmlFor="brand">Brand</label>
              <input
                id="brand"
                type="text"
                placeholder="e.g., Apple"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label htmlFor="minPrice">Min Price ($)</label>
              <input
                id="minPrice"
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label htmlFor="maxPrice">Max Price ($)</label>
              <input
                id="maxPrice"
                type="number"
                min="0"
                step="0.01"
                placeholder="1000.00"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
              />
            </div>
          </div>

          <h3>Location</h3>
          
          <div className="filter-grid">
            <div className="filter-group">
              <label htmlFor="zipCode">Zip Code</label>
              <input
                id="zipCode"
                type="text"
                placeholder="e.g., 10001"
                maxLength="5"
                value={zipCode}
                onChange={(e) => setZipCode(e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label htmlFor="radius">Radius (miles)</label>
              <select
                id="radius"
                value={radius}
                onChange={(e) => setRadius(e.target.value)}
              >
                <option value="5">5 miles</option>
                <option value="10">10 miles</option>
                <option value="25">25 miles</option>
                <option value="50">50 miles</option>
                <option value="100">100 miles</option>
              </select>
            </div>

            <div className="filter-group filter-checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={inStock}
                  onChange={(e) => setInStock(e.target.checked)}
                />
                In Stock Only
              </label>
            </div>
          </div>
        </div>

        <div className="search-actions">
          <button type="submit" className="btn-primary">
            Search
          </button>
          <button type="button" onClick={handleReset} className="btn-secondary">
            Reset
          </button>
        </div>
      </form>

      <div className="search-results">
        {loading && <div className="loading">Searching...</div>}
        
        {error && <div className="alert alert-error">{error}</div>}
        
        {!loading && !error && products.length === 0 && searchParams.toString() && (
          <div className="empty-state">
            <p>No products found matching your criteria.</p>
          </div>
        )}

        {!loading && products.length > 0 && (
          <>
            <p className="results-count">{products.length} product(s) found</p>
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default SearchPage
