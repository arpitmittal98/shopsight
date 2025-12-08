# 📋 ShopSight - Complete Feature Documentation

## Table of Contents
1. [Product Search Feature](#1-product-search-feature)
2. [Product Analytics Dashboard](#2-product-analytics-dashboard)
3. [Sales History Visualization](#3-sales-history-visualization)
4. [Demand Forecasting](#4-demand-forecasting)
5. [Customer Segmentation](#5-customer-segmentation)
6. [AI-Generated Insights](#6-ai-generated-insights)
7. [Data Sources & Loading](#7-data-sources--loading)

---

## 1. Product Search Feature

### Description
Natural language search interface that allows users to find products using conversational queries like "black running shoes" or "red summer dress".

### Data Sources

#### Real Data Used:
- **Source**: `s3://kumo-public-datasets/hm_with_images/articles/part-*.parquet`
- **Table**: Products DataFrame (`products_df`)
- **Columns Used**:
  - `article_id` (int64) - Unique product identifier
  - `prod_name` (string) - Product name
  - `product_type_name` (string) - Category (e.g., "Vest top", "Sneakers")
  - `product_group_name` (string) - Broader category
  - `colour_group_name` (string) - Color (e.g., "Black", "Red")
  - `department_name` (string) - Department (e.g., "Womens Everyday Basics")
  - `section_name` (string) - Section
  - `garment_group_name` (string) - Garment type
  - `image_url` (string) - Product image URL from S3

#### Sample Size:
- **Full dataset**: 105,542 products
- **Loaded in memory**: 105,542 products (complete catalog, no sampling)
- **Loading**: Direct from S3 using s3fs with pandas, no local file fallback

### Data Loading Process

```python
# File: backend/data_loader.py
def _load_data(self):
    # 1. S3 path to products (no local fallback)
    s3_path = 's3://kumo-public-datasets/hm_with_images/articles/'
    
    # 2. Load all parquet files from S3 with PyArrow + s3fs
    df = pd.read_parquet(s3_path, engine='pyarrow')
    
    # 3. Load full catalog - NO sampling
    self.products_df = df  # All 105,542 products
    
    # 4. Load real transaction data (476k records)
    transactions_path = 's3://kumo-public-datasets/hm_with_images/transactions/'
    self.transactions_df = pd.read_parquet(transactions_path, engine='pyarrow')
```

### Components & Dependencies

#### Backend Components:
1. **LLM Service** (`backend/llm_service.py`)
   - **LLM Call**: YES (Optional)
   - **Provider**: Google Gemini 2.0 Flash (primary), keyword fallback
   - **Purpose**: Parse natural language query into structured parameters
   - **Input**: "black running shoes for women"
   - **Output**: `{category: 'shoes', color: 'black', gender: 'women'}`
   - **Fallback**: Keyword-based regex parsing if LLM unavailable
   - **API Key**: `GEMINI_API_KEY` in `.env` file

2. **Data Loader** (`backend/data_loader.py`)
   - **Method**: `search_products(query, category, color, department, limit)`
   - **Search Algorithm**: 
     - Text matching with Pandas `str.contains()` (case-insensitive)
     - Searches across: `prod_name`, `product_type_name`, `product_group_name`
     - Filters by category, color, department if provided
   - **Returns**: List of product dictionaries (max 20 by default)

3. **Flask API** (`backend/app.py`)
   - **Endpoint**: `GET/POST /api/search`
   - **Query Params**: `?query=shoes&limit=20&category=&color=&department=`
   - **Response**: JSON with products array

#### Frontend Components:
1. **SearchBar.js** - Input field with submit button
2. **ProductCard.js** - Grid item displaying each product
3. **LoadingSkeleton.js** - Shimmer loading state during search
4. **App.js** - Orchestrates search flow

### User Flow
1. User types query: "black shoes"
2. Frontend sends to `/api/search?query=black+shoes`
3. Backend calls LLM to parse (or uses fallback)
4. Parsed params used to filter `products_df`
5. Results returned as JSON
6. Frontend displays in grid layout

### Performance
- **Search Time**: 50-200ms (in-memory Pandas filtering)
- **LLM Overhead**: +500-1500ms if enabled
- **Memory**: ~150MB for 10k products

---

## 2. Product Analytics Dashboard

### Description
Comprehensive analytics view shown when clicking a product card. Displays all metrics, charts, segments, and insights in one page.

### Data Sources

#### Real Data Used:
- **Source**: Same `products_df` from search
- **Columns**: All product metadata (name, type, color, department, etc.)
- **Purpose**: Display product details, inform analytics calculations

#### Mock Data Generated:
- **None directly** - This is a layout/visualization component
- **Aggregates data from**: Sales History, Forecasting, Segmentation modules

### Data Loading Process
```python
# File: backend/app.py - Route: /api/product/<article_id>
def get_product(article_id):
    # 1. Fetch product from products_df
    product = data_loader.get_product_by_id(article_id)
    
    # 2. Generate sales history (mock)
    sales_history = analytics.generate_sales_history(...)
    
    # 3. Generate forecast (mock)
    forecast = analytics.generate_forecast(...)
    
    # 4. Analyze segments (mock)
    segments = segmentation.analyze_product_segments(...)
    
    # 5. Generate AI insights (LLM)
    insights = llm_service.generate_insights(...)
    
    # 6. Return combined JSON
    return jsonify({product, sales, forecast, segments, personas, insights})
```

### Components & Dependencies

#### Backend Components:
1. **Data Loader** - Fetches product by ID
2. **Analytics Engine** - Generates sales & forecast
3. **Segmentation Engine** - Calculates customer segments
4. **LLM Service** - Generates insights text

#### Frontend Components:
1. **ProductDetails.js** - Main dashboard layout
2. **Chart.js** (via react-chartjs-2):
   - `Line` chart for sales history
   - `Doughnut` chart for customer segments
3. **CSS Animations** - Fade-in, hover effects

### LLM Usage
- **Call Made**: YES (for insights generation)
- **Optional**: Works without LLM (fallback text)

### Performance
- **Load Time**: 100-300ms (all calculations done synchronously)
- **Charts Render**: 50-100ms (Chart.js)

---

## 3. Sales History Visualization

### Description
Interactive line chart showing 12 months of historical sales data for a product. Displays units sold and revenue over time.

### Data Sources

#### Hybrid: Real Transaction Data + Mock Generation:
- **Real Data**: 476,039 transaction records from S3 (Sept 2018 - Sept 2020)
- **Coverage**: 58,360 products with real sales history (55% of catalog)
- **Mock Data**: Generated for remaining products without transaction history
- **Algorithm**: `backend/analytics.py` → `generate_sales_history()` routes to real or mock

#### Algorithm Details:
```python
def generate_sales_history(article_id, product_name, product_type, months=12):
    # 1. Check if real transaction data exists
    if data_loader.has_transaction_data():
        transactions = data_loader.get_product_transactions(article_id)
        
        if not transactions.empty:
            # Use REAL transaction data
            transactions['month'] = pd.to_datetime(transactions['t_dat']).dt.to_period('M')
            monthly = transactions.groupby('month').agg({
                'price': ['sum', 'count']
            })
            return {
                'dates': monthly.index.to_timestamp().strftime('%Y-%m').tolist(),
                'sales': monthly[('price', 'count')].tolist(),
                'revenue': monthly[('price', 'sum')].tolist(),
                'data_source': 'real'
            }
    
    # 2. Fallback to MOCK generation
    np.random.seed(article_id % 10000)
    
    # 3. Determine base sales from product type
    # - T-shirts: 800-1500 units/month
    # - Dresses: 400-900 units/month
    # - Jackets: 200-600 units/month
    
    # 4. Apply seasonal patterns
    # 5. Add growth trend and noise
    # 6. Calculate estimated revenue
    
    return {
        'dates': ['2024-01', '2024-02', ...],
        'sales': [850, 920, 780, ...],
        'data_source': 'mock'
    }
```

#### Seasonal Multipliers:
- **Coats/Jackets**: `[1.3, 1.2, 1.0, 0.7, 0.6, 0.5, 0.5, 0.6, 0.8, 1.1, 1.3, 1.4]`
- **Summer Wear**: `[0.6, 0.6, 0.8, 1.0, 1.2, 1.4, 1.5, 1.4, 1.1, 0.9, 0.7, 0.6]`
- **Dresses**: `[0.7, 0.7, 0.9, 1.1, 1.3, 1.4, 1.3, 1.2, 1.0, 0.9, 0.8, 0.9]`

### Components & Dependencies

#### Backend Components:
1. **Analytics Engine** (`backend/analytics.py`)
   - **Method**: `generate_sales_history()`
   - **LLM Required**: NO
   - **Deterministic**: YES (same article_id = same history)

2. **Flask API**
   - **Endpoint**: `/api/product/<article_id>` (includes sales data)

#### Frontend Components:
1. **ProductDetails.js** - Renders chart
2. **Chart.js** - Line chart with two datasets:
   - Historical sales (solid line, blue gradient)
   - Forecast (dashed line, purple - see next section)

### Metrics Calculated
```python
analytics.calculate_metrics(sales_data):
    # 1. Growth Rate: (recent 3mo - previous 3mo) / previous 3mo
    # 2. Peak Month: Month with highest sales
    # 3. Average Price: total_revenue / total_sales
    # 4. Volatility: (std_dev / mean) × 100
```

### Use Case
- **Investors**: Understand product performance trends
- **Inventory Managers**: Identify seasonal patterns
- **Marketing Teams**: Plan campaigns around peak periods

---

## 4. Demand Forecasting

### Description
Predicts next 3 months of sales using simple trend extrapolation. Includes confidence intervals (upper/lower bounds).

### Data Sources

#### Input: Mock Sales History
- **Source**: Output from `generate_sales_history()` (12 months)
- **Uses**: Last 12 data points to calculate trend

#### Algorithm:
```python
def generate_forecast(historical_sales, periods=3):
    # 1. Calculate linear trend slope
    x = [0, 1, 2, ..., 11]  # Time indices
    y = historical_sales     # Sales values
    slope = linear_regression(x, y)
    
    # 2. Extrapolate trend forward
    last_value = y[-1]
    forecast = [last_value + slope×1, last_value + slope×2, last_value + slope×3]
    
    # 3. Calculate std_dev from last 6 months
    std_dev = np.std(y[-6:])
    
    # 4. Confidence intervals (±1.96 × std_dev for 95% CI)
    upper = [forecast[i] + 1.96×std_dev for i in range(3)]
    lower = [forecast[i] - 1.96×std_dev for i in range(3)]
    
    return {
        'forecast': [850, 870, 890],
        'confidence_upper': [1100, 1120, 1140],
        'confidence_lower': [600, 620, 640],
        'trend': 'increasing' or 'decreasing',
        'trend_percentage': 12.3
    }
```

### Components & Dependencies

#### Backend Components:
1. **Analytics Engine** (`backend/analytics.py`)
   - **Method**: `generate_forecast()`
   - **LLM Required**: NO
   - **Dependencies**: NumPy for calculations

#### Frontend Components:
1. **ProductDetails.js** - Line chart extends with dashed line
2. **Forecast Cards** - 3 cards showing monthly predictions

### Limitations & Future Enhancements
- **Current**: Simple linear trend + noise
- **Production**: 
  - Facebook Prophet (seasonal decomposition)
  - ARIMA/SARIMA (autoregressive models)
  - LSTM neural networks (deep learning)
  - Kumo's Relational Forecasting Models

### Use Case
- **Inventory Planning**: Order stock based on predicted demand
- **Budget Allocation**: Allocate marketing spend to growing products
- **Risk Management**: Identify declining products early

---

## 5. Customer Segmentation

### Description
Identifies which customer segments are most likely to purchase a product and generates detailed buyer personas.

### Data Sources

#### Real Data Used:
- **Source**: `hm_with_images/part-00000-9b749c0f-095a-448e-b555-cbfb0bb7a01c-c000.snappy.parquet`
- **Table**: Customers DataFrame (`customers_df`)
- **Columns**:
  - `age` (float) - Customer age
  - `club_member_status` (string) - ACTIVE, PRE-CREATE, LEFT CLUB
  - `fashion_news_frequency` (string) - NONE, Regularly, Monthly
- **Sample Size**: 1,000 synthetic records (original 1.3M caused memory issues)

#### Mock/Calculated Data:
- **Segment Probabilities**: Rule-based calculation from product attributes
- **Buyer Personas**: Generated from templates

### Algorithm

#### Segment Probability Calculation:
```python
def _calculate_segment_probabilities(product_type, department, color):
    # Initialize equal probabilities
    probabilities = {
        'Fashion Forward': 1.0,
        'Classic Professional': 1.0,
        'Value Seeker': 1.0,
        'Active Lifestyle': 1.0,
        'Mature Sophisticate': 1.0
    }
    
    # Apply rules based on product attributes
    if 'sport' in product_type or 'athletic' in product_type:
        probabilities['Active Lifestyle'] *= 3.0
    
    if 'blazer' in product_type or 'shirt' in product_type:
        probabilities['Classic Professional'] *= 2.5
    
    if 'crop' in product_type or 'graphic' in product_type:
        probabilities['Fashion Forward'] *= 3.0
    
    if 'black' in color or 'white' in color:
        probabilities['Classic Professional'] *= 1.5
    
    if 'bright' in color or 'neon' in color:
        probabilities['Fashion Forward'] *= 2.0
    
    # Normalize to sum to 100%
    total = sum(probabilities.values())
    return {k: (v/total)*100 for k, v in probabilities.items()}
```

#### Segment Definitions:
1. **Fashion Forward** (18-30): Trend-conscious, early adopters, social media active
2. **Classic Professional** (30-45): Quality-focused, timeless styles, brand loyal
3. **Value Seeker** (25-50): Price-conscious, sale shoppers, practical
4. **Active Lifestyle** (20-40): Athletic wear, comfort-focused, wellness-oriented
5. **Mature Sophisticate** (45+): Premium quality, refined taste, loyalty members

#### Persona Generation:
```python
def generate_buyer_personas(segment_analysis, sales_metrics):
    # For top 3 segments (>10% probability):
    for segment_name, probability in top_segments:
        persona = {
            'name': template_name,  # e.g., 'Emma' for Fashion Forward
            'segment': segment_name,
            'probability': probability,
            'age_range': segment_info['age_range'],
            'occupation': template['occupation'],
            'shopping_behavior': template['shopping_behavior'],
            'price_sensitivity': 'Low' | 'Medium' | 'High',
            'preferred_channels': 'Online' | 'In-store' | etc.
        }
```

### Components & Dependencies

#### Backend Components:
1. **Segmentation Engine** (`backend/segmentation.py`)
   - **Methods**: `analyze_product_segments()`, `generate_buyer_personas()`
   - **LLM Required**: NO
   - **Data Required**: Product attributes only (no customer history)

#### Frontend Components:
1. **ProductDetails.js** - Doughnut chart + persona cards
2. **Chart.js** - Doughnut/pie chart showing segment distribution

### Use Case
- **Marketing Teams**: Target ads to specific demographics
- **Product Development**: Design features for key segments
- **Pricing Strategy**: Set prices based on segment price sensitivity
- **Retail Planning**: Stock inventory based on local demographics

---

## 6. AI-Generated Insights

### Description
Natural language summary of product performance, trends, and recommendations generated by LLM or fallback algorithm.

### Data Sources

#### Input Data (All Mock):
- Sales history (from Analytics Engine)
- Forecast data (from Analytics Engine)
- Segment analysis (from Segmentation Engine)

#### LLM Integration:

##### With Gemini 2.0 Flash:
```python
def generate_insights(product_name, sales_data, forecast_data, segment_data):
    # Prepare context
    context = f"""
    Product: {product_name}
    Total Sales (12mo): {sales_data['total_sales']} units
    Growth Rate: {sales_data['growth_rate']}%
    Forecast Trend: {forecast_data['trend']} ({forecast_data['trend_percentage']}%)
    Top Segment: {segment_data['top_segment']} ({segment_data['probability']}%)
    Data Source: {sales_data.get('data_source', 'mock')}  # 'real' or 'mock'
    """
    
    # Call Gemini 2.0 Flash
    import google.generativeai as genai
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""You are an e-commerce analytics expert. Analyze this product and provide:
    1. Sales performance assessment
    2. Growth opportunities
    3. Customer targeting recommendations
    Keep under 150 words, use ## for section headings.
    
    {context}"""
    
    response = model.generate_content(prompt)
    return response.text
```

##### Fallback (No LLM):
```python
def _fallback_insights(product_name, sales_data, forecast_data, segment_data):
    insights = f"{product_name} has sold {sales_data['total_sales']:,} units over the past 12 months"
    
    if growth_rate > 10:
        insights += f" with strong growth of {growth_rate}%"
    
    insights += f". The product is {trend}"
    
    if trend == 'increasing':
        insights += " and forecast shows continued growth opportunity"
    
    insights += f". Primary customer segment is {top_segment} ({probability}%), "
    
    if growth_rate > 15:
        insights += " Consider increasing inventory to meet growing demand."
    
    return insights
```

### Components & Dependencies

#### Backend Components:
1. **LLM Service** (`backend/llm_service.py`)
   - **Method**: `generate_insights()`
   - **LLM Required**: OPTIONAL (has fallback)
   - **Providers Supported**: Google Gemini 2.0 Flash
   - **Cost**: ~$0.0001 per product view (Gemini 2.0 Flash)

2. **Environment Configuration**:
   - `GEMINI_API_KEY` in `.env`

#### Frontend Components:
1. **ProductDetails.js** - Gradient card displaying insights
2. **CSS Animations** - Floating orb background effect

### Example Outputs

#### With LLM:
> "This Strap top demonstrates strong market performance with 8,450 units sold over 12 months, showing impressive 18.5% growth. The upward trend is expected to continue with forecasts predicting 15-20% increase in Q1. The product resonates particularly well with Fashion Forward customers (45.8%), suggesting opportunities for social media marketing and influencer partnerships. Peak sales in November indicate strong holiday season demand. Recommendation: Increase inventory by 20% ahead of next holiday season and consider expanding color options to capture broader Fashion Forward segment."

#### Fallback (No LLM):
> "Strap top has sold 8,450 units over the past 12 months with strong growth of 18.5%. The product is increasing and forecast shows continued growth opportunity. Primary customer segment is Fashion Forward (45.8% of buyers), indicating strong market fit. Consider increasing inventory to meet growing demand."

### Use Case
- **Executive Summaries**: Quick understanding without reading charts
- **Action Items**: Direct recommendations for decision-makers
- **Conversational Analytics**: Makes data accessible to non-technical users

---

## 7. Data Sources & Loading

### Complete Data Inventory

#### A. Product Catalog (Real)
- **Source**: `s3://kumo-public-datasets/hm_with_images/articles/`
- **Size**: ~80MB compressed, ~350MB in memory
- **Rows**: 105,542 products
- **Loaded**: 105,542 products (full dataset, no sampling)
- **Format**: Apache Parquet (columnar)
- **Engine**: PyArrow with s3fs
- **Loading Time**: 8-11 seconds (direct from S3)

#### B. Transaction Data (Real)
- **Source**: `s3://kumo-public-datasets/hm_with_images/transactions/part-00000-*.parquet`
- **Size**: ~200MB in memory (1 of 69 partitions loaded)
- **Rows**: 476,039 transaction records
- **Date Range**: September 2018 - September 2020
- **Coverage**: 58,360 unique products with sales history
- **Format**: Apache Parquet (columnar)
- **Columns**: article_id, customer_id, t_dat (date), price, sales_channel_id
- **Loading Time**: 3-5 seconds (direct from S3)

**Schema**:
```
article_id: int64                      # 108775015
prod_name: string                      # "Strap top"
product_type_no: int64                 # 253
product_type_name: string              # "Vest top"
product_group_name: string             # "Garment Upper body"
graphical_appearance_no: int64         # 1010016
graphical_appearance_name: string      # "Solid"
colour_group_code: int64               # 9
colour_group_name: string              # "Black"
perceived_colour_value_id: int64       # 4
perceived_colour_value_name: string    # "Dark"
perceived_colour_master_id: int64      # 5
perceived_colour_master_name: string   # "Black"
department_no: int64                   # 1002
department_name: string                # "Jersey Basic"
index_code: string                     # "A"
index_name: string                     # "Ladieswear"
index_group_no: int64                  # 1
index_group_name: string               # "Ladieswear"
section_no: int64                      # 16
section_name: string                   # "Womens Everyday Basics"
garment_group_no: int64                # 1002
garment_group_name: string             # "Jersey Basic"
image_url: string                      # "https://kumo-public-datasets.s3..."
```

#### C. Product Images (Real)
- **Source**: S3 bucket `kumo-public-datasets`
- **Path**: `hm_with_images/*.jpg`
- **Count**: ~1,000 images
- **Format**: JPEG
- **Access**: Direct URLs in `image_url` column
- **Loading**: Lazy-loaded by browser (not backend)

#### D. Customer Demographics (Not Currently Used)
- **Available**: Customer data exists in S3 but not loaded
- **Segmentation**: Uses product attributes instead of customer history
- **Future**: Can integrate real customer clustering from transaction patterns

### Loading Strategy

#### Initialization (App Startup):
```python
# backend/app.py
data_loader = DataLoader()           # Loads full 105k product catalog from S3
analytics = SalesAnalytics()         # No data loaded (stateless)
segmentation = CustomerSegmentation() # No data loaded (stateless)
llm_service = LLMService()           # Initializes API client
```

#### Per-Request (Product View):
```python
# /api/product/<article_id>
1. Fetch product from products_df (O(1) with index)
2. Generate sales history (compute, ~10ms)
3. Generate forecast (compute, ~5ms)
4. Analyze segments (compute, ~5ms)
5. Generate personas (compute, ~5ms)
6. Call LLM for insights (network, ~500-1500ms)
7. Return JSON
```

### Memory Footprint

| Component | Memory | Notes |
|-----------|--------|-------|
| products_df (105k) | ~350 MB | Full catalog |
| transactions_df (476k) | ~200 MB | Real sales data |
| Flask app | ~50 MB | Base overhead |
| Gemini SDK | ~10 MB | Google GenAI |
| **Total** | **~610 MB** | Requires 2GB+ RAM |

### Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| App startup | 3-5s | Load products |
| Search (no LLM) | 50-200ms | Pandas filter |
| Search (with LLM) | 500-1500ms | +LLM parsing |
| Product details (no LLM) | 100-300ms | All calculations |
| Product details (with LLM) | 600-1800ms | +LLM insights |
| Chart rendering (frontend) | 50-100ms | Chart.js |

---

## Summary Table

| Feature | Real Data | Mock Data | LLM Required | Components | Use Case |
|---------|-----------|-----------|--------------|------------|----------|
| **Product Search** | Products catalog (105k) | None | Optional | DataLoader, LLMService, SearchBar.js | Find products by query |
| **Analytics Dashboard** | Product metadata | None | Optional | All modules, ProductDetails.js | View comprehensive insights |
| **Sales History** | Transactions (476k, 58k products) | Fallback for remaining 45% | No | Analytics, Chart.js Line | Understand past performance |
| **Demand Forecast** | Uses real sales when available | Trend extrapolation | No | Analytics, Chart.js Line | Plan inventory |
| **Customer Segments** | None | Probability rules, personas | No | Segmentation, Chart.js Doughnut | Target marketing |
| **AI Insights** | Uses real/mock sales data | Fallback text | Optional | Gemini 2.0 Flash | Executive summary |

---

## Key Takeaways

1. **Full product catalog loaded** - All 105,542 products from H&M dataset
2. **Real transaction data integrated** - 476,039 records covering 58,360 products (55%)
3. **Hybrid analytics approach** - Real data when available, intelligent mock fallback
4. **Gemini 2.0 Flash integration** - Latest AI model for insights and search parsing
5. **Direct S3 loading** - No local files needed, production-ready cloud architecture
6. **Fast responses** - 100-300ms without LLM, 600-1800ms with AI insights
7. **Data source transparency** - Clear labeling of 'real' vs 'mock' data
8. **Scalable foundation** - Ready to expand to more transaction partitions (69 available)
