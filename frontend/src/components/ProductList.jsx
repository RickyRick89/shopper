import ProductCard from './ProductCard'

function ProductList({ products, loading, error, emptyMessage }) {
  if (loading) {
    return <div className="loading">Loading products...</div>
  }

  if (error) {
    return <div className="alert alert-error">{error}</div>
  }

  if (!products || products.length === 0) {
    return (
      <div className="empty-state">
        <p>{emptyMessage || 'No products found.'}</p>
      </div>
    )
  }

  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}

export default ProductList
