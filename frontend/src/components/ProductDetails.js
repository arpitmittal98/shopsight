import React from 'react';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';
import './ProductDetails.css';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function ProductDetails({ data, onBack, loading }) {
  if (loading || !data) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading product analytics...</p>
      </div>
    );
  }

  const { product, sales, forecast, segments, personas, insights } = data;

  // Prepare sales chart data with real forecast month labels
  const forecastLabels = forecast.forecast_months || ['Next', 'Next+1', 'Next+2'];
  const salesChartData = {
    labels: [...sales.dates, ...forecastLabels],
    datasets: [
      {
        label: 'Historical Sales',
        data: [...sales.sales],
        borderColor: 'rgb(102, 126, 234)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Forecast',
        // Start forecast from the last historical point to connect the lines
        data: [...Array(sales.sales.length - 1).fill(null), sales.sales[sales.sales.length - 1], ...forecast.forecast],
        borderColor: 'rgb(118, 75, 162)',
        backgroundColor: 'rgba(118, 75, 162, 0.1)',
        borderDash: [5, 5],
        tension: 0.4,
        fill: true,
      }
    ]
  };

  const salesChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Sales History & Forecast'
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Units Sold'
        }
      }
    }
  };

  // Prepare segment chart data
  const segmentChartData = {
    labels: Object.keys(segments.segments),
    datasets: [{
      data: Object.values(segments.segments),
      backgroundColor: [
        'rgba(255, 107, 107, 0.8)',
        'rgba(78, 205, 196, 0.8)',
        'rgba(255, 230, 109, 0.8)',
        'rgba(149, 225, 211, 0.8)',
        'rgba(168, 218, 220, 0.8)',
      ],
      borderWidth: 0,
    }]
  };

  const segmentChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Customer Segments'
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return context.label + ': ' + context.parsed + '%';
          }
        }
      }
    }
  };

  return (
    <div className="product-details">
      <button className="back-button" onClick={onBack}>
        Back to Search
      </button>

      <div className="details-header">
        <div className="header-image">
          {product.image_url ? (
            <img src={product.image_url} alt={product.prod_name} />
          ) : (
            <div className="image-placeholder">📦</div>
          )}
        </div>
        <div className="header-info">
          <h1>{product.prod_name}</h1>
          <p className="product-meta">
            {product.product_type_name} • {product.department_name}
          </p>
          <div className="product-attributes">
            <span className="attribute">🎨 {product.colour_group_name}</span>
            <span className="attribute">📦 ID: {product.article_id}</span>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="insights-section">
        <h2>🤖 AI Insights</h2>
        <div className="insights-card">
          {data.insightsLoading ? (
            <div className="insights-loading">
              <div className="spinner-small"></div>
              <p>Generating smart analysis...</p>
            </div>
          ) : (
          <div className="insights-content">
            {(() => {
              // Parse markdown-style insights
              if (!insights) return <p className="insight-text">No insights available.</p>;
              const lines = insights.split('\n').filter(line => line.trim());
              const elements = [];
              
              lines.forEach((line, idx) => {
                const trimmed = line.trim();
                
                // Heading (## Title)
                if (trimmed.startsWith('##')) {
                  elements.push(
                    <h3 key={`h-${idx}`} className="insight-heading">
                      {trimmed.replace(/^##\s*/, '').replace(/[:#]+$/, '')}
                    </h3>
                  );
                }
                // Bullet point (- Item)
                else if (trimmed.startsWith('-')) {
                  elements.push(
                    <div key={`b-${idx}`} className="insight-bullet">
                      <span className="bullet-point">•</span>
                      <span dangerouslySetInnerHTML={{ 
                        __html: trimmed.substring(1).trim().replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') 
                      }} />
                    </div>
                  );
                }
                // Numbered list (1. Item)
                else if (/^\d+\./.test(trimmed)) {
                  const match = trimmed.match(/^(\d+)\./); 
                  const number = match ? match[1] : '1';
                  elements.push(
                    <div key={`n-${idx}`} className="insight-numbered">
                      <span className="number-badge">{number}</span>
                      <span dangerouslySetInnerHTML={{ 
                        __html: trimmed.replace(/^\d+\.\s*/, '').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') 
                      }} />
                    </div>
                  );
                }
                // Regular paragraph
                else if (trimmed.length > 0) {
                  elements.push(
                    <p key={`p-${idx}`} className="insight-text" dangerouslySetInnerHTML={{ 
                      __html: trimmed.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') 
                    }} />
                  );
                }
              });
              
              return elements;
            })()}
          </div>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{sales.total_sales.toLocaleString()}</div>
          <div className="metric-label">
            Total Sales (12mo)
            {sales.data_source && (
              <span className={`data-badge ${sales.data_source}`}>
                {sales.data_source === 'real' ? '📊 Real Data' : '🎲 Generated'}
              </span>
            )}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-value">${sales.total_revenue.toLocaleString()}</div>
          <div className="metric-label">Total Revenue</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{sales.growth_rate}%</div>
          <div className="metric-label">Growth Rate</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{sales.avg_monthly_sales}</div>
          <div className="metric-label">Avg Monthly Sales</div>
        </div>
      </div>

      {/* Sales Chart */}
      <div className="chart-section">
        <div className="chart-container">
          <Line data={salesChartData} options={salesChartOptions} />
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="two-column">
        {/* Customer Segments */}
        <div className="segment-section">
          <h2>👥 Customer Segments</h2>
          <div className="chart-container-small">
            <Doughnut data={segmentChartData} options={segmentChartOptions} />
          </div>
          <div className="segment-details">
            <p>
              <strong>Top Segment:</strong> {segments.top_segment} ({segments.top_segment_probability}%)
            </p>
          </div>
        </div>

        {/* Buyer Personas */}
        <div className="persona-section">
          <h2>🎯 Buyer Personas</h2>
          <div className="personas-list">
            {personas.map((persona, idx) => (
              <div key={idx} className="persona-card">
                <h3>{persona.name} - {persona.segment}</h3>
                <div className="persona-detail">
                  <span className="persona-label">Age:</span> {persona.age_range}
                </div>
                <div className="persona-detail">
                  <span className="persona-label">Occupation:</span> {persona.occupation}
                </div>
                <div className="persona-detail">
                  <span className="persona-label">Behavior:</span> {persona.shopping_behavior}
                </div>
                <div className="persona-detail">
                  <span className="persona-label">Price Sensitivity:</span> {persona.price_sensitivity}
                </div>
                <div className="persona-probability">
                  {persona.probability}% likely to purchase
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Forecast Summary */}
      <div className="forecast-section">
        <h2>📈 Forecast (Next 3 Months)</h2>
        <div className="forecast-grid">
          {forecast.forecast.map((value, idx) => (
            <div key={idx} className="forecast-card">
              <div className="forecast-label">{forecast.forecast_months?.[idx] || `Month ${idx + 1}`}</div>
              <div className="forecast-value">{value} units</div>
              <div className="forecast-range">
                Range: {forecast.confidence_lower[idx]} - {forecast.confidence_upper[idx]}
              </div>
            </div>
          ))}
        </div>
        <p className="forecast-trend">
          <strong>Trend:</strong> {forecast.trend} ({forecast.trend_percentage}%)
        </p>
      </div>
    </div>
  );
}

export default ProductDetails;
