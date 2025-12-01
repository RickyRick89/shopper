import { Link } from 'react-router-dom'
import { useContext } from 'react'
import { AuthContext } from '../App'

function Header() {
  const { user, logout } = useContext(AuthContext)

  return (
    <header className="header">
      <Link to="/" className="header-logo">
        🛒 Shopper
      </Link>
      <nav className="header-nav">
        <Link to="/">Home</Link>
        <Link to="/products">Products</Link>
        {user && <Link to="/wishlist">Wishlist</Link>}
      </nav>
      <div className="header-auth">
        {user ? (
          <>
            <span>Hi, {user.full_name || user.email}</span>
            <button onClick={logout} className="btn-secondary">
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login">
              <button className="btn-secondary">Login</button>
            </Link>
            <Link to="/register">
              <button className="btn-primary">Sign Up</button>
            </Link>
          </>
        )}
      </div>
    </header>
  )
}

export default Header
