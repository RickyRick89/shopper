import { useState, useEffect } from 'react'
import ProductCard from '../components/ProductCard'
import SearchBar from '../components/SearchBar'
import { apiService } from '../services/api'

function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProducts = async (query = '') => {
    setLoading(true)
    try {
      const data = await apiService.getProducts(query)
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
