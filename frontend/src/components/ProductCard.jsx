import { Link } from 'react-router-dom'

function ProductCard({ product }) {
  const lowestPrice = product.prices && product.prices.length > 0
    ? Math.min(...product.prices.map((p) => p.price))
    : null

  return (
    <div className="product-card">
      <h3>{product.name}</h3>
      <p>{product.brand}</p>
      {product.description && (
        <p>{product.description.substring(0, 100)}...</p>
      )}
      {lowestPrice !== null ? (
        <div className="product-price">${lowestPrice.toFixed(2)}</div>
      ) : (
        <div className="product-retailer">No price data</div>
      )}
      <Link to={`/products/${product.id}`}>
        <button style={{ marginTop: '1rem', width: '100%' }}>View Details</button>
      </Link>
    </div>
  )
}

export default ProductCard
