const API_BASE_URL = '/api/v1'

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token')
  }

  setToken(token) {
    this.token = token
  }

  getHeaders(includeAuth = false) {
    const headers = {
      'Content-Type': 'application/json',
    }
    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    return headers
  }

  async get(endpoint, requiresAuth = false) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: requiresAuth ? this.getHeaders(true) : {},
    })
    if (!response.ok) throw new Error('Request failed')
    return response.json()
  }

  async post(endpoint, data, requiresAuth = false) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(requiresAuth),
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Request failed')
    }
    return response.json()
  }

  async delete(endpoint, requiresAuth = false) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(requiresAuth),
    })
    if (!response.ok) throw new Error('Request failed')
    return response
  }

  // Products
  async getProducts(query = '') {
    const params = query ? `?query=${encodeURIComponent(query)}` : ''
    return this.get(`/products${params}`)
  }

  async getProduct(id) {
    return this.get(`/products/${id}`)
  }

  // Auth
  async register(userData) {
    return this.post('/auth/register', userData)
  }

  async login(email, password) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }
    return response.json()
  }

  // Wishlist
  async getWishlist() {
    return this.get('/wishlist', true)
  }

  async addToWishlist(productId, targetPrice = null) {
    return this.post('/wishlist', { product_id: productId, target_price: targetPrice }, true)
  }

  async removeFromWishlist(itemId) {
    return this.delete(`/wishlist/${itemId}`, true)
  }

  // Search
  async searchProducts(params = {}) {
    const searchParams = new URLSearchParams()
    if (params.q) searchParams.append('q', params.q)
    if (params.category) searchParams.append('category', params.category)
    if (params.brand) searchParams.append('brand', params.brand)
    if (params.min_price) searchParams.append('min_price', params.min_price)
    if (params.max_price) searchParams.append('max_price', params.max_price)
    if (params.retailer) searchParams.append('retailer', params.retailer)
    if (params.in_stock) searchParams.append('in_stock', 'true')
    if (params.zip_code) searchParams.append('zip_code', params.zip_code)
    if (params.radius) searchParams.append('radius', params.radius)
    if (params.page) searchParams.append('page', params.page)
    if (params.limit) searchParams.append('limit', params.limit)

    const queryString = searchParams.toString()
    return this.get(`/search/products${queryString ? '?' + queryString : ''}`)
  }

  async getSearchSuggestions(query) {
    return this.get(`/search/suggestions?q=${encodeURIComponent(query)}`)
  }

  async getDeals(params = {}) {
    const searchParams = new URLSearchParams()
    if (params.category) searchParams.append('category', params.category)
    if (params.max_price) searchParams.append('max_price', params.max_price)
    if (params.page) searchParams.append('page', params.page)
    if (params.limit) searchParams.append('limit', params.limit)

    const queryString = searchParams.toString()
    return this.get(`/search/deals${queryString ? '?' + queryString : ''}`)
  }
}

export const apiService = new ApiService()
export default apiService
