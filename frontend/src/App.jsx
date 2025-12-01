import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect, createContext } from 'react'
import Header from './components/Header'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import Wishlist from './pages/Wishlist'
import './styles/App.css'

export const AuthContext = createContext(null)

function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      // Fetch current user
      fetch('/api/v1/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
        .then((res) => {
          if (res.ok) return res.json()
          throw new Error('Invalid token')
        })
        .then((data) => setUser(data))
        .catch(() => {
          localStorage.removeItem('token')
          setToken(null)
          setUser(null)
        })
    }
  }, [token])

  const login = (accessToken) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <Router>
        <div className="app">
          <Header />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:id" element={<ProductDetail />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/wishlist" element={<Wishlist />} />
            </Routes>
          </main>
          <footer className="footer">
            <p>&copy; 2024 Shopper - Find the Best Deals</p>
          </footer>
        </div>
      </Router>
    </AuthContext.Provider>
  )
}

export default App
