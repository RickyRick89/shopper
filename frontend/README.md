# Shopper Frontend

React-based web interface for the Shopper application, built with Vite.

## Features

- **Home Page**: Landing page with feature highlights
- **Product Browsing**: Search and browse products
- **Product Details**: View product info and price comparisons
- **User Authentication**: Login and registration
- **Wishlist**: Save products and manage target prices

## Setup

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

## Build

```bash
npm run build
```

## Lint

```bash
npm run lint
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Header.jsx
│   │   ├── ProductCard.jsx
│   │   └── SearchBar.jsx
│   ├── pages/           # Page components
│   │   ├── Home.jsx
│   │   ├── Products.jsx
│   │   ├── ProductDetail.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   └── Wishlist.jsx
│   ├── services/        # API service
│   ├── styles/          # CSS styles
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── index.html           # HTML template
├── package.json         # Dependencies
└── vite.config.js       # Vite configuration
```

## Connecting to Backend

The frontend is configured to proxy API requests to `http://localhost:8000`.
Make sure the backend is running before using authentication or data features.
