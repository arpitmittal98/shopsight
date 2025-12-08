import React from 'react';
import './ProductCard.css';

function ProductCard({ product, onClick }) {
  return (
    <div className="product-card" onClick={onClick}>
      <div className="product-image-container">
        {product.image_url ? (
          <img 
            src={product.image_url} 
            alt={product.prod_name}
            className="product-image"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/300x400?text=No+Image';
            }}
          />
        ) : (
          <div className="product-image-placeholder">
            <span>📦</span>
          </div>
        )}
      </div>
      
      <div className="product-info">
        <h3 className="product-name">{product.prod_name}</h3>
        <p className="product-type">{product.product_type_name}</p>
        
        <div className="product-tags">
          {product.colour_group_name && (
            <span className="tag">{product.colour_group_name}</span>
          )}
          {product.department_name && (
            <span className="tag">{product.department_name}</span>
          )}
        </div>
        
        <button className="view-details-btn">
          View Analytics →
        </button>
      </div>
    </div>
  );
}

export default ProductCard;
