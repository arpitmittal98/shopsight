# Backend

Python backend for ShopSight analytics platform.

## Structure

- `app.py` - Main Flask API server
- `data_loader.py` - H&M dataset loading and querying
- `analytics.py` - Sales analytics and forecasting
- `segmentation.py` - Customer segment analysis
- `llm_service.py` - Multi-LLM integration (Gemini 2.0 Flash, Hugging Face Llama 3.1 8B)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp ../.env.example ../.env
# Edit .env and add your LLM API key
```

3. Run the server:
```bash
python app.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### `GET /api/search?query=<text>`
Search products with natural language

### `GET /api/product/<article_id>`
Get detailed product analytics (with `?skip_insights=true` for fast load)

### `GET /api/product/<article_id>/insights`
Get AI-generated insights for a product (async endpoint)

### `GET /api/analytics/<article_id>`
Get sales analytics for a product

### `GET /api/segments/<article_id>`
Get customer segments for a product

### `GET /api/filters`
Get available filter options (categories, colors, departments)

### `GET /api/demographics`
Get overall customer demographics
