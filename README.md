# ShopSight - AI E-commerce Analytics

Natural language product search with real-time analytics and AI-powered insights using H&M's 105k+ product catalog and 476k transaction records.

## Thought Process & Priorities

**1. Real Data First** - Loaded full S3 dataset (105k products, 476k transactions) to demonstrate production-ready integration, not toy examples.

**2. User Experience** - Prioritized natural language search with LLM parsing over rigid filters. Users type "red dress" instead of clicking category dropdowns.

**3. Intelligent Trade-offs** - Lazy-load transactions on analytics view (not upfront) for instant startup. Use 1/69 partition (55% coverage) vs 15-min load time. I had originally started with loading only 1 section of transaction data (~1%) but I thought we could load data only for that product ID when clicks on the tile v/s loading small data for all the products at once. 

**4. Progressive Enhancement** - Real data where available, intelligent mocks for gaps. UI clearly shows data source ("📊 Real Data" vs "🎲 Generated"). For the demo. 

**5. Production Mindset** - Structured logging, retry logic, error handling, responsive UI design. 

## Key Assumptions

- **Search patterns**: Users prefer natural language ("black shoes") over structured filters for such a large dataset.
- **Analytics demand**: Not all products need analytics immediately → lazy load transactions
- **Data quality**: 55% real transaction coverage sufficient for demo; mock data indistinguishable to users
- **Use fallbacks for uninterrupted demo**: Use LLM fallbacks, forecasting fallbacks (if very few transactional data points for that product) 
- **Latency tolerance**: 3s initial load acceptable; analytics views can take 2-3s. I had started with loading everything at once and changed later.

## How to Run Locally

### Prerequisites
- Python 3.8+, Node.js 16+
- LLM API key: Google Gemini (recommended, free) or Hugging Face (Llama 3.1 8B)
  - Gemini: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
  - Hugging Face: Get from [Hugging Face Tokens](https://huggingface.co/settings/tokens)

### Quick Start

```bash
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Set up API key (in project root)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY or HUGGINGFACE_API_KEY

# 4. Start backend (Terminal 1)
cd backend && python app.py

# 5. Start frontend (Terminal 2)
cd frontend && npm start

# 6. Open http://localhost:3000
```

**First run**: Backend loads 105k products from S3 (~11 seconds). Subsequent starts use cached data.

**Without API key**: Search works with keyword fallback; AI insights show basic summaries.

## What's Real vs Mocked

### Real Data (S3)
- **Product Catalog**: 105,542 items - all attributes, images, categories
- **Transactions**: 476,039 records (Sept 2018 - Sept 2020) - actual sales, prices, dates
- **Sales History**: 58,360 products (55%) use real transaction aggregation
- **LLM Parsing**: Google Gemini 2.0 Flash or Hugging Face Llama 3.1 8B - live API calls for query understanding

### Mocked Data (Intelligent Generation)
- **Sales History**: 45% of products without transactions (or very less transactions) -> generated data points
- **Forecasting**: Linear trend extrapolation - can use time series in the future like ARIMA
- **Customer Demographics**: 1,000 synthetic customers for demographic analytics
- **Segmentation**: Rule-based personas - can implement clustering algos. 

**Data Source Indicators**: UI shows 📊 "Real Data" or 🎲 "Generated" badges on metric cards.

## Tech Stack

**Backend**: Flask 3.0, Pandas 2.1, Google Gemini 2.0 Flash / Hugging Face Llama 3.1 8B, S3FS (direct S3 access)  
**Frontend**: React 18, Chart.js 4.4, CSS3 responsive design  
**Data**: H&M Parquet files on AWS S3 (`s3://kumo-public-datasets/hm_with_images/`)  
**LLM**: Gemini 2.0 Flash (primary) or Hugging Face Llama 3.1 8B Instruct for NLP parsing and insights; keyword fallback when unavailable

---

## Implementation Gaps & Production Approach

### Not Implemented (with Strategy)

**1. Advanced Forecasting Models with Real Data**
- **Gap**: Simple linear trend → No seasonality, external factors
- **Approach**: Integrate Prophet (Facebook) for seasonal decomposition; ARIMA for auto-regressive patterns; XGBoost for feature-rich predictions (price, promotions, holidays)

**2. Real Customer Data Integration**
- **Gap**: Mock demographics → Can't segment by actual purchase behavior
- **Approach**: Load real customer data from S3 (`customers.parquet`); run K-means clustering on RFM (Recency, Frequency, Monetary); use embeddings for behavioral segmentation

**3. Non-functional requirements**
- **Gap**: Missing performance, scalability data for taking it to production.
- **Approach**: Add NFR such as performance, API security (so customer data isn't exposed), availablity, scalability etc. 

**4. Add Pagination in the UI**
- **Gap**: Currently, I have set a limit of max 20 products in search result for demo.
- **Approach**: Add pagination in the UI with proper tracking of already displayed products.

---

## Architecture Decisions

**Lazy Transaction Loading**: Load on analytics click (not upfront) → Instant startup vs 15-min wait  
**Linear Forecasting**: Simple but explainable → Fast prototyping; Prophet upgrade adds 20% accuracy  
**Client-Side Rendering**: React SPA → Simple deployment; Next.js would add SEO but overkill for internal tool  
**Multi-LLM Support**: Gemini 2.0 Flash or Hugging Face Llama 3.1 8B (free) → Flexible provider choice with fallback

---

