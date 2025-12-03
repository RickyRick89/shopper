import { useState, useEffect } from 'react'

/**
 * PriceHistoryChart component displays price history data for a product.
 * Shows a visual representation of price changes over time with statistics.
 */
function PriceHistoryChart({ productId, priceHistory, isLoading, error }) {
  const [chartData, setChartData] = useState([])
  const [stats, setStats] = useState(null)
  const [selectedRetailer, setSelectedRetailer] = useState('all')

  useEffect(() => {
    if (priceHistory && priceHistory.data) {
      // Group data by retailer if needed
      let filteredData = priceHistory.data
      if (selectedRetailer !== 'all') {
        filteredData = priceHistory.data.filter(
          (point) => point.retailer === selectedRetailer
        )
      }
      setChartData(filteredData)
      setStats(priceHistory.stats)
    }
  }, [priceHistory, selectedRetailer])

  // Get unique retailers from data
  const retailers = priceHistory?.data
    ? [...new Set(priceHistory.data.map((point) => point.retailer))]
    : []

  // Calculate chart dimensions based on data
  const getChartPath = () => {
    if (!chartData || chartData.length === 0) return ''

    const prices = chartData.map((d) => d.price)
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    const priceRange = maxPrice - minPrice || 1

    const chartWidth = 100
    const chartHeight = 100
    const padding = 5

    const points = chartData.map((point, index) => {
      const x = padding + (index / (chartData.length - 1 || 1)) * (chartWidth - 2 * padding)
      const y = chartHeight - padding - ((point.price - minPrice) / priceRange) * (chartHeight - 2 * padding)
      return `${x},${y}`
    })

    return `M${points.join(' L')}`
  }

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  // Format price for display
  const formatPrice = (price) => {
    if (price === null || price === undefined) return 'N/A'
    return `$${price.toFixed(2)}`
  }

  // Get trend indicator
  const getTrendIndicator = () => {
    if (!stats || stats.price_change_pct === null) return null

    const change = stats.price_change_pct
    if (change > 0) {
      return { icon: '↑', color: '#ff4444', text: 'up' }
    } else if (change < 0) {
      return { icon: '↓', color: '#4caf50', text: 'down' }
    }
    return { icon: '→', color: '#888', text: 'stable' }
  }

  const trend = getTrendIndicator()

  if (isLoading) {
    return (
      <div className="price-history-chart">
        <div className="chart-loading">Loading price history...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="price-history-chart">
        <div className="chart-error">{error}</div>
      </div>
    )
  }

  if (!priceHistory || !priceHistory.data || priceHistory.data.length === 0) {
    return (
      <div className="price-history-chart">
        <h3>Price History</h3>
        <div className="chart-empty">
          No price history available yet. Price data will be collected over time.
        </div>
      </div>
    )
  }

  return (
    <div className="price-history-chart">
      <div className="chart-header">
        <h3>Price History</h3>
        {retailers.length > 1 && (
          <select
            value={selectedRetailer}
            onChange={(e) => setSelectedRetailer(e.target.value)}
            className="retailer-select"
          >
            <option value="all">All Retailers</option>
            {retailers.map((retailer) => (
              <option key={retailer} value={retailer}>
                {retailer}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="chart-container">
        <svg
          viewBox="0 0 100 100"
          className="price-chart-svg"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <line x1="5" y1="25" x2="95" y2="25" stroke="#333" strokeWidth="0.2" />
          <line x1="5" y1="50" x2="95" y2="50" stroke="#333" strokeWidth="0.2" />
          <line x1="5" y1="75" x2="95" y2="75" stroke="#333" strokeWidth="0.2" />

          {/* Price line */}
          <path
            d={getChartPath()}
            fill="none"
            stroke="#646cff"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Data points */}
          {chartData.map((point, index) => {
            const prices = chartData.map((d) => d.price)
            const minPrice = Math.min(...prices)
            const maxPrice = Math.max(...prices)
            const priceRange = maxPrice - minPrice || 1
            const chartWidth = 100
            const chartHeight = 100
            const padding = 5

            const x = padding + (index / (chartData.length - 1 || 1)) * (chartWidth - 2 * padding)
            const y = chartHeight - padding - ((point.price - minPrice) / priceRange) * (chartHeight - 2 * padding)

            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="1.5"
                fill="#646cff"
              />
            )
          })}
        </svg>

        <div className="chart-labels">
          <span className="chart-label-start">
            {formatDate(chartData[0]?.date)}
          </span>
          <span className="chart-label-end">
            {formatDate(chartData[chartData.length - 1]?.date)}
          </span>
        </div>
      </div>

      {stats && (
        <div className="price-stats">
          <div className="stat-item">
            <span className="stat-label">Current</span>
            <span className="stat-value current">
              {formatPrice(stats.current_price)}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Lowest</span>
            <span className="stat-value low">{formatPrice(stats.min_price)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Highest</span>
            <span className="stat-value high">{formatPrice(stats.max_price)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Average</span>
            <span className="stat-value">{formatPrice(stats.avg_price)}</span>
          </div>
          {trend && (
            <div className="stat-item">
              <span className="stat-label">Trend</span>
              <span className="stat-value trend" style={{ color: trend.color }}>
                {trend.icon} {Math.abs(stats.price_change_pct).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      )}

      <style>{`
        .price-history-chart {
          background-color: #2a2a2a;
          border-radius: 12px;
          padding: 1.5rem;
          margin-top: 1.5rem;
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .chart-header h3 {
          margin: 0;
        }

        .retailer-select {
          padding: 0.5rem;
          border-radius: 6px;
          background-color: #1a1a1a;
          border: 1px solid #444;
          color: white;
          font-size: 0.875rem;
        }

        .chart-container {
          position: relative;
          height: 200px;
          background-color: #1a1a1a;
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: 1rem;
        }

        .price-chart-svg {
          width: 100%;
          height: 100%;
        }

        .chart-labels {
          display: flex;
          justify-content: space-between;
          position: absolute;
          bottom: 0.5rem;
          left: 1rem;
          right: 1rem;
          font-size: 0.75rem;
          color: #888;
        }

        .price-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
          gap: 1rem;
        }

        .stat-item {
          text-align: center;
          padding: 0.75rem;
          background-color: #1a1a1a;
          border-radius: 8px;
        }

        .stat-label {
          display: block;
          font-size: 0.75rem;
          color: #888;
          margin-bottom: 0.25rem;
        }

        .stat-value {
          font-size: 1rem;
          font-weight: bold;
        }

        .stat-value.current {
          color: #646cff;
        }

        .stat-value.low {
          color: #4caf50;
        }

        .stat-value.high {
          color: #ff9800;
        }

        .stat-value.trend {
          font-size: 0.9rem;
        }

        .chart-loading,
        .chart-error,
        .chart-empty {
          text-align: center;
          padding: 2rem;
          color: #888;
        }

        .chart-error {
          color: #ff4444;
        }
      `}</style>
    </div>
  )
}

export default PriceHistoryChart
