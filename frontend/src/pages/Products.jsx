import { useState, useEffect } from 'react'
import ProductList from '../components/ProductList'
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
      <ProductList
        products={products}
        loading={loading}
        error={error}
        emptyMessage="No products found. Try a different search term."
      />
    </div>
  )
}

export default Products
