"""
Analytics Module
Generates sales trends, forecasts, and insights using REAL transaction data.
Falls back to mock data if transactions not available.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional
import random


class SalesAnalytics:
    def __init__(self, data_loader=None):
        self.base_seed = 42
        self.data_loader = data_loader
    
    def generate_sales_history(
        self, 
        article_id: int,
        product_name: str,
        product_type: str,
        months: int = 12
    ) -> Dict:
        """
        Generate sales history for a product.
        Uses REAL transaction data if available, otherwise generates mock data.
        """
        # Try to use real transaction data first
        if self.data_loader and self.data_loader.has_transaction_data():
            real_data = self._generate_real_sales_history(article_id, months)
            if real_data is not None:
                return real_data
        
        # Fallback to mock data generation
        return self._generate_mock_sales_history(article_id, product_name, product_type, months)
    
    def _generate_real_sales_history(self, article_id: int, months: int = 12) -> Optional[Dict]:
        """Generate sales history from real transaction data."""
        try:
            # Get transactions for this product
            transactions = self.data_loader.get_product_transactions(article_id)
            
            if transactions is None or len(transactions) == 0:
                return None
            
            # Need at least 6 months of data for meaningful analytics
            # If less, fall back to mock data for better visualization
            unique_months = transactions['t_dat'].dt.to_period('M').nunique()
            if unique_months < 6:
                return None
            
            # Group by month
            transactions['month'] = transactions['t_dat'].dt.to_period('M')
            monthly_data = transactions.groupby('month').agg({
                'price': ['sum', 'count']
            }).reset_index()
            
            monthly_data.columns = ['month', 'revenue', 'sales']
            monthly_data['month'] = monthly_data['month'].dt.to_timestamp()
            
            # Sort by date
            monthly_data = monthly_data.sort_values('month')
            
            # Get last N months
            if len(monthly_data) > months:
                monthly_data = monthly_data.tail(months)
            
            dates = monthly_data['month'].dt.strftime('%Y-%m').tolist()
            sales = monthly_data['sales'].astype(int).tolist()
            revenue = monthly_data['revenue'].round(2).tolist()
            
            return {
                'dates': dates,
                'sales': sales,
                'revenue': revenue,
                'total_sales': sum(sales),
                'total_revenue': round(sum(revenue), 2),
                'avg_monthly_sales': round(sum(sales) / len(sales), 1),
                'data_source': 'real'
            }
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error generating real sales history: {e}")
            return None
    
    def _generate_mock_sales_history(
        self, 
        article_id: int,
        product_name: str,
        product_type: str,
        months: int = 12
    ) -> Dict:
        """
        Generate realistic mock sales history for a product.
        Uses product characteristics to create believable patterns.
        """
        # Seed based on article_id for consistency
        np.random.seed(article_id % 10000)
        
        # Base sales volume depends on product type
        base_sales = self._get_base_sales_by_type(product_type)
        
        # Generate monthly data
        end_date = datetime.now()
        dates = []
        sales = []
        revenue = []
        
        # Seasonal patterns
        seasonal_factor = self._get_seasonal_pattern(product_type)
        
        for i in range(months):
            date = end_date - timedelta(days=30 * (months - i - 1))
            dates.append(date.strftime('%Y-%m'))
            
            # Add trend (slight growth/decline)
            trend = 1 + (i / months) * random.uniform(-0.2, 0.3)
            
            # Add seasonality
            month_idx = (date.month - 1) % 12
            season_multiplier = seasonal_factor[month_idx]
            
            # Add random noise
            noise = np.random.normal(1, 0.15)
            
            # Calculate sales
            monthly_sales = int(base_sales * trend * season_multiplier * noise)
            monthly_sales = max(10, monthly_sales)  # Minimum 10 sales
            
            # Calculate revenue (assume price range based on product type)
            avg_price = self._get_avg_price_by_type(product_type)
            monthly_revenue = monthly_sales * avg_price * np.random.uniform(0.9, 1.1)
            
            sales.append(monthly_sales)
            revenue.append(round(monthly_revenue, 2))
        
        return {
            'dates': dates,
            'sales': sales,
            'revenue': revenue,
            'total_sales': sum(sales),
            'total_revenue': round(sum(revenue), 2),
            'avg_monthly_sales': round(sum(sales) / len(sales), 1),
            'data_source': 'mock'
        }
    
    def generate_forecast(
        self,
        historical_sales: List[int],
        periods: int = 3
    ) -> Dict:
        """
        Generate sales forecast based on historical data.
        Uses simple trend analysis with confidence intervals.
        """
        if len(historical_sales) < 3:
            return {'forecast': [], 'confidence_upper': [], 'confidence_lower': []}
        
        # Calculate trend
        x = np.arange(len(historical_sales))
        y = np.array(historical_sales)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        last_value = y[-1]
        
        forecast = []
        confidence_upper = []
        confidence_lower = []
        
        # Standard deviation for confidence interval
        std_dev = np.std(y[-6:]) if len(y) >= 6 else np.std(y)
        
        for i in range(1, periods + 1):
            # Trend-based forecast
            predicted = last_value + (slope * i)
            # Add some uncertainty
            predicted = max(0, predicted + np.random.normal(0, std_dev * 0.1))
            
            forecast.append(int(predicted))
            confidence_upper.append(int(predicted + 1.96 * std_dev))
            confidence_lower.append(max(0, int(predicted - 1.96 * std_dev)))
        
        # Generate month labels for forecast (match historical format YYYY-MM)
        current_date = datetime.now()
        forecast_months = []
        for i in range(1, periods + 1):
            future_date = current_date + relativedelta(months=i)
            forecast_months.append(future_date.strftime('%Y-%m'))  # e.g., "2026-01"
        
        return {
            'forecast': forecast,
            'confidence_upper': confidence_upper,
            'confidence_lower': confidence_lower,
            'forecast_months': forecast_months,  # ['Jan 2026', 'Feb 2026', 'Mar 2026']
            'trend': 'increasing' if slope > 0 else 'decreasing',
            'trend_percentage': round((slope / np.mean(y)) * 100, 1) if np.mean(y) > 0 else 0
        }
    
    def calculate_metrics(self, sales_data: Dict) -> Dict:
        """Calculate key performance metrics."""
        sales = sales_data['sales']
        revenue = sales_data['revenue']
        
        # Growth rate (last 3 months vs previous 3 months)
        if len(sales) >= 6:
            recent = sum(sales[-3:])
            previous = sum(sales[-6:-3])
            growth_rate = ((recent - previous) / previous * 100) if previous > 0 else 0
        else:
            growth_rate = 0
        
        # Peak month
        peak_idx = sales.index(max(sales))
        peak_month = sales_data['dates'][peak_idx]
        
        return {
            'growth_rate': round(growth_rate, 1),
            'peak_month': peak_month,
            'peak_sales': max(sales),
            'avg_price': round(sum(revenue) / sum(sales), 2) if sum(sales) > 0 else 0,
            'volatility': round(np.std(sales) / np.mean(sales) * 100, 1) if np.mean(sales) > 0 else 0
        }
    
    def _get_base_sales_by_type(self, product_type: str) -> int:
        """Determine base sales volume based on product type."""
        product_type_lower = product_type.lower() if product_type else ""
        
        if any(word in product_type_lower for word in ['t-shirt', 'top', 'vest']):
            return random.randint(800, 1500)
        elif any(word in product_type_lower for word in ['dress', 'skirt']):
            return random.randint(400, 900)
        elif any(word in product_type_lower for word in ['jacket', 'coat']):
            return random.randint(200, 600)
        elif any(word in product_type_lower for word in ['shoe', 'sneaker', 'boot']):
            return random.randint(300, 800)
        elif any(word in product_type_lower for word in ['jean', 'trouser', 'pant']):
            return random.randint(500, 1000)
        else:
            return random.randint(300, 800)
    
    def _get_avg_price_by_type(self, product_type: str) -> float:
        """Determine average price based on product type."""
        product_type_lower = product_type.lower() if product_type else ""
        
        if any(word in product_type_lower for word in ['t-shirt', 'top', 'vest']):
            return random.uniform(15, 35)
        elif any(word in product_type_lower for word in ['dress', 'skirt']):
            return random.uniform(30, 70)
        elif any(word in product_type_lower for word in ['jacket', 'coat']):
            return random.uniform(60, 150)
        elif any(word in product_type_lower for word in ['shoe', 'sneaker', 'boot']):
            return random.uniform(40, 100)
        elif any(word in product_type_lower for word in ['jean', 'trouser', 'pant']):
            return random.uniform(35, 80)
        else:
            return random.uniform(20, 60)
    
    def _get_seasonal_pattern(self, product_type: str) -> List[float]:
        """
        Get seasonal multipliers for each month (Jan-Dec).
        Different product types have different seasonal patterns.
        """
        product_type_lower = product_type.lower() if product_type else ""
        
        # Winter clothing (coats, jackets)
        if any(word in product_type_lower for word in ['jacket', 'coat', 'sweater']):
            return [1.3, 1.2, 1.0, 0.7, 0.6, 0.5, 0.5, 0.6, 0.8, 1.1, 1.3, 1.4]
        
        # Summer clothing (shorts, t-shirts, swimwear)
        elif any(word in product_type_lower for word in ['short', 'swim', 'bikini', 'tank']):
            return [0.6, 0.6, 0.8, 1.0, 1.2, 1.4, 1.5, 1.4, 1.1, 0.9, 0.7, 0.6]
        
        # Dresses (spring/summer peak)
        elif 'dress' in product_type_lower:
            return [0.7, 0.7, 0.9, 1.1, 1.3, 1.4, 1.3, 1.2, 1.0, 0.9, 0.8, 0.9]
        
        # Shoes (relatively stable)
        elif any(word in product_type_lower for word in ['shoe', 'sneaker', 'boot']):
            return [0.9, 0.9, 1.0, 1.1, 1.1, 1.0, 0.9, 0.9, 1.0, 1.1, 1.2, 1.1]
        
        # Default (slight seasonal variation)
        else:
            return [0.9, 0.9, 1.0, 1.0, 1.1, 1.1, 1.0, 1.0, 1.0, 1.1, 1.1, 1.0]


if __name__ == "__main__":
    # Test the analytics module
    analytics = SalesAnalytics()
    
    # Generate sample sales history
    history = analytics.generate_sales_history(
        article_id=108775015,
        product_name="Strap top",
        product_type="Vest top",
        months=12
    )
    
    print("Sales History:")
    print(f"Total Sales: {history['total_sales']}")
    print(f"Total Revenue: ${history['total_revenue']}")
    print(f"Avg Monthly Sales: {history['avg_monthly_sales']}")
    
    # Generate forecast
    forecast = analytics.generate_forecast(history['sales'], periods=3)
    print(f"\nForecast (next 3 months): {forecast['forecast']}")
    print(f"Trend: {forecast['trend']} ({forecast['trend_percentage']}%)")
    
    # Calculate metrics
    metrics = analytics.calculate_metrics(history)
    print(f"\nMetrics:")
    print(f"Growth Rate: {metrics['growth_rate']}%")
    print(f"Peak Month: {metrics['peak_month']}")
