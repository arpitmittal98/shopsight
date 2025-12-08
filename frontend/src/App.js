import React, { useState, useEffect } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import ProductCard from './components/ProductCard';
import ProductDetails from './components/ProductDetails';
import LoadingSkeleton from './components/LoadingSkeleton';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_URL}/api/search`, {
        params: { query, limit: 20 }
      });
      setSearchResults(response.data.results || []);
    } catch (err) {
      console.error('Search error:', err);
      setError('Failed to search products. Please ensure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = async (product) => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch product data without insights first (fast load)
      const response = await axios.get(`${API_URL}/api/product/${product.article_id}?skip_insights=true`);
      const data = response.data;
      data.insightsLoading = true; // Flag to show loading state
      setSelectedProduct(data);
      setLoading(false);
      
      // Then fetch insights asynchronously
      try {
        const insightsResponse = await axios.get(`${API_URL}/api/product/${product.article_id}/insights`);
        setSelectedProduct(prev => ({
          ...prev,
          insights: insightsResponse.data.insights,
          insightsLoading: false
        }));
      } catch (insightsErr) {
        console.error('Insights fetch error:', insightsErr);
        setSelectedProduct(prev => ({
          ...prev,
          insights: 'Unable to generate AI insights at this time.',
          insightsLoading: false
        }));
      }
    } catch (err) {
      console.error('Product fetch error:', err);
      setError('Failed to load product details.');
      setLoading(false);
    }
  };

  const handleBackToSearch = () => {
    setSelectedProduct(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1 onClick={() => { setSearchResults([]); setSearchQuery(''); setSelectedProduct(null); }} style={{ cursor: 'pointer' }}>
            ShopSight
          </h1>
          <p className="tagline">AI-Powered E-commerce Analytics</p>
        </div>
      </header>

      <main className="App-main">
        {!selectedProduct ? (
          <>
            <div className="search-section">
              <SearchBar 
                value={searchQuery}
                onChange={setSearchQuery}
                onSearch={handleSearch}
                loading={loading}
              />
              <p className="search-hint">
                Try searching: "black shoes", "red dress", "running gear"
              </p>
            </div>

            {error && (
              <div className="error-message">
                <span>⚠️ {error}</span>
              </div>
            )}

            {loading && searchQuery && (
              <LoadingSkeleton type="grid" />
            )}

            {!loading && searchResults.length > 0 && (
              <div className="results-section">
                <h2>Found {searchResults.length} products</h2>
                <div className="products-grid">
                  {searchResults.map((product) => (
                    <ProductCard
                      key={product.article_id}
                      product={product}
                      onClick={() => handleProductClick(product)}
                    />
                  ))}
                </div>
              </div>
            )}

            {!loading && searchQuery && searchResults.length === 0 && (
              <div className="no-results">
                <p>No products found. Try a different search term.</p>
              </div>
            )}
          </>
        ) : (
          <ProductDetails
            data={selectedProduct}
            onBack={handleBackToSearch}
            loading={loading}
          />
        )}
      </main>

      <footer className="App-footer">
        <p>ShopSight Demo - Powered by AI & Real Data</p>
      </footer>
    </div>
  );
}

export default App;
