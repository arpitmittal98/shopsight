import React from 'react';
import './LoadingSkeleton.css';

function LoadingSkeleton({ type = 'card' }) {
  if (type === 'card') {
    return (
      <div className="skeleton-card">
        <div className="skeleton-image"></div>
        <div className="skeleton-content">
          <div className="skeleton-title"></div>
          <div className="skeleton-text"></div>
          <div className="skeleton-tags">
            <div className="skeleton-tag"></div>
            <div className="skeleton-tag"></div>
          </div>
          <div className="skeleton-button"></div>
        </div>
      </div>
    );
  }

  if (type === 'grid') {
    return (
      <div className="skeleton-grid">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <LoadingSkeleton key={i} type="card" />
        ))}
      </div>
    );
  }

  return null;
}

export default LoadingSkeleton;
