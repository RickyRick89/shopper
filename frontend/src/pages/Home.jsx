import { Link } from 'react-router-dom'

function Home() {
  return (
    <div className="home-page">
      <section className="hero">
        <h1>Find the Best Deals</h1>
        <p>Track prices, compare retailers, and never miss a deal again.</p>
        <Link to="/products">
          <button className="btn-primary">Start Shopping</button>
        </Link>
      </section>

      <section className="features">
        <div className="feature-card">
          <h3>🔍 Price Tracking</h3>
          <p>Monitor prices across multiple retailers and get notified when they drop.</p>
        </div>
        <div className="feature-card">
          <h3>📊 Price History</h3>
          <p>View historical price trends to make informed purchasing decisions.</p>
        </div>
        <div className="feature-card">
          <h3>❤️ Wishlist</h3>
          <p>Save items you're interested in and set target prices for alerts.</p>
        </div>
        <div className="feature-card">
          <h3>🔔 Price Alerts</h3>
          <p>Get notified instantly when products reach your target price.</p>
        </div>
      </section>
    </div>
  )
}

export default Home
