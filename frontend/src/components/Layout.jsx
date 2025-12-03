import Header from './Header'

function Layout({ children }) {
  return (
    <div className="app">
      <Header />
      <main className="main-content">
        {children}
      </main>
      <footer className="footer">
        <p>&copy; 2024 Shopper - Find the Best Deals</p>
      </footer>
    </div>
  )
}

export default Layout
