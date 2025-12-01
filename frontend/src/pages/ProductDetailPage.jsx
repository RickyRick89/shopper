import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiService } from '../services/api'

function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState(null)
  const [relatedProducts, setRelatedProducts] = useState([])

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        const data = await apiService.getProduct(id)
        setProduct(data)

        // Fetch related products by category
        if (data.category) {
          try {
            const related = await apiService.searchProducts({ category: data.category })
            // Filter out the current product and limit to 4
            setRelatedProducts(
              related.filter(p => p.id !== data.id).slice(0, 4)
            )
          } catch {
            // Ignore errors for related products
          }
        }
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

  const getLowestPrice = () => {
    if (!product?.prices || product.prices.length === 0) return null
    const inStockPrices = product.prices.filter(p => p.in_stock)
    if (inStockPrices.length === 0) return null
    return Math.min(...inStockPrices.map(p => p.price))
  }

  const getHighestPrice = () => {
    if (!product?.prices || product.prices.length === 0) return null
    const inStockPrices = product.prices.filter(p => p.in_stock)
    if (inStockPrices.length === 0) return null
    return Math.max(...inStockPrices.map(p => p.price))
  }

  if (loading) return <div className="loading">Loading product details...</div>
  if (error) return <div className="alert alert-error">{error}</div>
  if (!product) return <div className="empty-state">Product not found</div>

  const lowestPrice = getLowestPrice()
  const highestPrice = getHighestPrice()
  const savings = lowestPrice && highestPrice ? (highestPrice - lowestPrice).toFixed(2) : null

  return (
    <div className="product-detail-page">
      <nav className="breadcrumb">
        <Link to="/">Home</Link>
        <span> / </span>
        <Link to="/products">Products</Link>
        <span> / </span>
        {product.category && (
          <>
            <Link to={`/search?category=${encodeURIComponent(product.category)}`}>
              {product.category}
            </Link>
            <span> / </span>
          </>
        )}
        <span>{product.name}</span>
      </nav>

      <div className="product-detail">
        <div className="product-image">
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} />
          ) : (
            <div className="no-image">No Image Available</div>
          )}
        </div>
        
        <div className="product-info">
          <h1>{product.name}</h1>
          
          {product.brand && (
            <p className="product-brand">
              <strong>Brand:</strong>{' '}
              <Link to={`/search?brand=${encodeURIComponent(product.brand)}`}>
                {product.brand}
              </Link>
            </p>
          )}
          
          {product.category && (
            <p className="product-category">
              <strong>Category:</strong>{' '}
              <Link to={`/search?category=${encodeURIComponent(product.category)}`}>
                {product.category}
              </Link>
            </p>
          )}
          
          {product.description && (
            <div className="product-description">
              <h3>Description</h3>
              <p>{product.description}</p>
            </div>
          )}

          {lowestPrice && (
            <div className="price-summary">
              <span className="lowest-price">${lowestPrice.toFixed(2)}</span>
              {savings && parseFloat(savings) > 0 && (
                <span className="savings">Save up to ${savings}</span>
              )}
            </div>
          )}

          {message && (
            <div className={`alert alert-${message.type}`}>{message.text}</div>
          )}

          <div className="product-actions">
            <button onClick={addToWishlist} className="btn-primary">
              ❤️ Add to Wishlist
            </button>
          </div>

          <div className="price-comparison">
            <h2>Price Comparison</h2>
            {product.prices && product.prices.length > 0 ? (
              <table className="price-table">
                <thead>
                  <tr>
                    <th>Retailer</th>
                    <th>Price</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {product.prices
                    .sort((a, b) => a.price - b.price)
                    .map((price) => (
                      <tr key={price.id} className={!price.in_stock ? 'out-of-stock' : ''}>
                        <td>{price.retailer}</td>
                        <td className="price-cell">
                          ${price.price.toFixed(2)}
                          {price.price === lowestPrice && (
                            <span className="best-price-badge">Best Price</span>
                          )}
                        </td>
                        <td>
                          <span className={`stock-status ${price.in_stock ? 'in-stock' : 'out-of-stock'}`}>
                            {price.in_stock ? 'In Stock' : 'Out of Stock'}
                          </span>
                        </td>
                        <td>
                          {price.url ? (
                            <a href={price.url} target="_blank" rel="noopener noreferrer" className="btn-small">
                              View
                            </a>
                          ) : (
                            <span className="no-link">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            ) : (
              <p>No price data available yet.</p>
            )}
          </div>
        </div>
      </div>

      {relatedProducts.length > 0 && (
        <div className="related-products">
          <h2>Related Products</h2>
          <div className="product-grid">
            {relatedProducts.map((relatedProduct) => (
              <div key={relatedProduct.id} className="product-card">
                <h3>{relatedProduct.name}</h3>
                <p>{relatedProduct.brand}</p>
                <Link to={`/products/${relatedProduct.id}`}>
                  <button className="btn-secondary btn-full-width">View Details</button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ProductDetailPage
