import { useState, useEffect } from 'react'
import ProductCard from '../components/ProductCard'
import SearchBar from '../components/SearchBar'

function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProducts = async (query = '') => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (query) params.append('query', query)
      
      const response = await fetch(`/api/v1/products?${params}`)
      if (!response.ok) throw new Error('Failed to fetch products')
      const data = await response.json()
      setProducts(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [])

  const handleSearch = (query) => {
    fetchProducts(query)
  }

  return (
    <div className="products-page">
      <h1 className="page-title">Products</h1>
      <SearchBar onSearch={handleSearch} />

      {loading && <div className="loading">Loading products...</div>}
      
      {error && <div className="alert alert-error">{error}</div>}
      
      {!loading && !error && products.length === 0 && (
        <div className="empty-state">
          <p>No products found. Try a different search term.</p>
        </div>
      )}

      <div className="product-grid">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  )
}

export default Products
