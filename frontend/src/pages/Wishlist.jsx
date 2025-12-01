import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiService } from '../services/api'

function Wishlist() {
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [wishlist, setWishlist] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }

    const fetchWishlist = async () => {
      try {
        apiService.setToken(token)
        const data = await apiService.getWishlist()
        setWishlist(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchWishlist()
  }, [user, token, navigate])

  const removeFromWishlist = async (itemId) => {
    try {
      apiService.setToken(token)
      await apiService.removeFromWishlist(itemId)
      setWishlist(wishlist.filter((item) => item.id !== itemId))
    } catch (err) {
      setError(err.message)
    }
  }

  if (!user) return null
  if (loading) return <div className="loading">Loading wishlist...</div>

  return (
    <div className="wishlist-page">
      <h1 className="page-title">My Wishlist</h1>

      {error && <div className="alert alert-error">{error}</div>}

      {wishlist.length === 0 ? (
        <div className="empty-state">
          <p>Your wishlist is empty.</p>
          <Link to="/products">
            <button className="btn-primary" style={{ marginTop: '1rem' }}>
              Browse Products
            </button>
          </Link>
        </div>
      ) : (
        <div>
          {wishlist.map((item) => (
            <div key={item.id} className="wishlist-item">
              <div className="wishlist-item-info">
                <Link to={`/products/${item.product.id}`}>
                  <h3>{item.product.name}</h3>
                </Link>
                {item.target_price && (
                  <p>Target Price: ${item.target_price.toFixed(2)}</p>
                )}
                {item.product.brand && <p>Brand: {item.product.brand}</p>}
              </div>
              <div className="wishlist-actions">
                <Link to={`/products/${item.product.id}`}>
                  <button className="btn-secondary">View</button>
                </Link>
                <button
                  onClick={() => removeFromWishlist(item.id)}
                  className="btn-danger"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Wishlist
