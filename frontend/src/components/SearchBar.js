import React from 'react';
import './SearchBar.css';

function SearchBar({ value, onChange, onSearch, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(value);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      onSearch(value);
    }
  };

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit}>
        <div className="search-input-wrapper">
          <input
            type="text"
            className="search-input"
            placeholder="Search for products (e.g., 'black running shoes')..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button 
            type="submit" 
            className="search-button"
            disabled={loading || !value.trim()}
          >
            {loading ? '🔄' : '🔍'} Search
          </button>
        </div>
      </form>
    </div>
  );
}

export default SearchBar;
