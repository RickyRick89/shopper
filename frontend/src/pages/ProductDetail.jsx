import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiService } from '../services/api'

function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const data = await apiService.getProduct(id)
        setProduct(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchProduct()
  }, [id])

  const addToWishlist = async () => {
    if (!user) {
      navigate('/login')
      return
    }

    try {
      apiService.setToken(token)
      await apiService.addToWishlist(parseInt(id))
      setMessage({ type: 'success', text: 'Added to wishlist!' })
    } catch (err) {
      if (err.message.includes('already in wishlist')) {
        setMessage({ type: 'error', text: 'Product already in wishlist' })
      } else {
        setMessage({ type: 'error', text: err.message })
      }
    }
  }

  if (loading) return <div className="loading">Loading...</div>
  if (error) return <div className="alert alert-error">{error}</div>
  if (!product) return <div className="empty-state">Product not found</div>

  return (
    <div className="product-detail">
      <div className="product-image">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} />
        ) : (
          <span>No Image Available</span>
        )}
      </div>
      <div className="product-info">
        <h1>{product.name}</h1>
        {product.brand && <p><strong>Brand:</strong> {product.brand}</p>}
        {product.category && <p><strong>Category:</strong> {product.category}</p>}
        {product.description && <p>{product.description}</p>}

        {message && (
          <div className={`alert alert-${message.type}`}>{message.text}</div>
        )}

        <button onClick={addToWishlist} className="btn-primary" style={{ marginTop: '1rem' }}>
          ❤️ Add to Wishlist
        </button>

        <div className="price-comparison">
          <h2>Price Comparison</h2>
          {product.prices && product.prices.length > 0 ? (
            <ul className="price-list">
              {product.prices
                .sort((a, b) => a.price - b.price)
                .map((price) => (
                  <li key={price.id} className="price-item">
                    <span>{price.retailer}</span>
                    <span className="product-price">${price.price.toFixed(2)}</span>
                  </li>
                ))}
            </ul>
          ) : (
            <p>No price data available yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProductDetail
