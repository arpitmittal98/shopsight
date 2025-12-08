"""
ShopSight Flask API
Main backend server providing product search, analytics, and insights.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

from data_loader import DataLoader
from analytics import SalesAnalytics
from segmentation import CustomerSegmentation
from llm_service import LLMService

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Initialize services
print("Initializing ShopSight services...")
data_loader = DataLoader()
analytics = SalesAnalytics(data_loader=data_loader)  # Pass data_loader for real transaction data
segmentation = CustomerSegmentation()
llm_service = LLMService()
print("✓ All services initialized\n")


@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        'status': 'online',
        'service': 'ShopSight API',
        'version': '1.0.0'
    })


@app.route('/api/search', methods=['GET', 'POST'])
def search_products():
    """
    Search products with natural language or filters.
    
    Query params (GET) or JSON body (POST):
    - query: Natural language search query
    - category: Product category filter
    - color: Color filter
    - department: Department filter
    - limit: Max results (default: 20)
    """
    if request.method == 'POST':
        data = request.json or {}
        query = data.get('query', '')
    else:
        query = request.args.get('query', '')
    
    limit = int(request.args.get('limit', 20))
    
    # Use LLM to parse query if available
    parsed_query = {}
    if query:
        parsed_query = llm_service.parse_search_query(query)
        print(f"🔍 Query: '{query}' -> Parsed: {parsed_query}")
    
    # Extract search parameters
    search_params = {
        'limit': limit
    }
    
    # Add parsed parameters
    if parsed_query.get('category'):
        search_params['category'] = parsed_query['category']
    if parsed_query.get('color'):
        search_params['color'] = parsed_query['color']
    
    # Override with explicit filters if provided
    if request.args.get('category'):
        search_params['category'] = request.args.get('category')
    if request.args.get('color'):
        search_params['color'] = request.args.get('color')
    if request.args.get('department'):
        search_params['department'] = request.args.get('department')
    
    # Add query text for keyword search
    # Use keywords from LLM parsing if available, otherwise use raw query
    if query:
        if parsed_query.get('keywords'):
            # Use keywords extracted by LLM (excludes category/color words)
            # This preserves brand names like "nike" while filtering structural words
            search_params['query'] = ' '.join(parsed_query['keywords'])
        else:
            # Fallback to raw query if no parsing occurred
            search_params['query'] = query
    
    # Perform search
    results = data_loader.search_products(**search_params)
    print(f"📊 Search params: {search_params} -> Found {len(results)} results")
    
    return jsonify({
        'query': query,
        'parsed': parsed_query,
        'count': len(results),
        'results': results  # Changed from 'products' to 'results' to match frontend
    })


@app.route('/api/product/<int:article_id>', methods=['GET'])
def get_product(article_id):
    """Get detailed product information with analytics."""
    # import time
    # start = time.time()
    
    # Get product data
    # t1 = time.time()
    product = data_loader.get_product_by_id(article_id)
    # print(f"⏱ Product fetch: {(time.time()-t1)*1000:.0f}ms")
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Generate sales analytics (may trigger lazy transaction loading)
    # t2 = time.time()
    sales_history = analytics.generate_sales_history(
        article_id=article_id,
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        months=12
    )
    # print(f"⏱ Sales history: {(time.time()-t2)*1000:.0f}ms")
    
    # Generate forecast
    # t3 = time.time()
    forecast = analytics.generate_forecast(sales_history['sales'], periods=3)
    # print(f"⏱ Forecast: {(time.time()-t3)*1000:.0f}ms")
    
    # Calculate metrics
    # t4 = time.time()
    metrics = analytics.calculate_metrics(sales_history)
    sales_history.update(metrics)
    # print(f"⏱ Metrics: {(time.time()-t4)*1000:.0f}ms")
    
    # Analyze customer segments
    # t5 = time.time()
    segments = segmentation.analyze_product_segments(
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        department=product.get('department_name', ''),
        color_group=product.get('colour_group_name', '')
    )
    # print(f"⏱ Segments: {(time.time()-t5)*1000:.0f}ms")
    
    # Generate buyer personas
    # t6 = time.time()
    personas = segmentation.generate_buyer_personas(segments, metrics)
    # print(f"⏱ Personas: {(time.time()-t6)*1000:.0f}ms")
    
    # Generate AI insights (slowest part - LLM call)
    # Skip if requested for faster initial load
    skip_insights = request.args.get('skip_insights', 'false').lower() == 'true'
    
    if skip_insights:
        insights = None
        # print(f"⏱ LLM Insights: SKIPPED")
    else:
        # t7 = time.time()
        insights = llm_service.generate_insights(
            product_name=product['prod_name'],
            sales_data=sales_history,
            forecast_data=forecast,
            segment_data=segments
        )
        # print(f"⏱ LLM Insights: {(time.time()-t7)*1000:.0f}ms")
    
    # print(f"⏱ TOTAL: {(time.time()-start)*1000:.0f}ms")
    
    return jsonify({
        'product': product,
        'sales': sales_history,
        'forecast': forecast,
        'segments': segments,
        'personas': personas,
        'insights': insights
    })


@app.route('/api/product/<int:article_id>/insights', methods=['GET'])
def get_product_insights(article_id):
    """Generate AI insights for a product (can be called asynchronously)."""
    # import time
    # start = time.time()
    
    # Get product data
    product = data_loader.get_product_by_id(article_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Get sales history and forecast
    sales_history = analytics.generate_sales_history(
        article_id=article_id,
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        months=12
    )
    forecast = analytics.generate_forecast(sales_history['sales'], periods=3)
    metrics = analytics.calculate_metrics(sales_history)
    sales_history.update(metrics)
    
    # Get segments
    segments = segmentation.analyze_product_segments(
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        department=product.get('department_name', ''),
        color_group=product.get('colour_group_name', '')
    )
    
    # Generate AI insights
    insights = llm_service.generate_insights(
        product_name=product['prod_name'],
        sales_data=sales_history,
        forecast_data=forecast,
        segment_data=segments
    )
    
    # print(f"⏱ Insights generation: {(time.time()-start)*1000:.0f}ms")
    
    return jsonify({
        'insights': insights
    })


@app.route('/api/analytics/<int:article_id>', methods=['GET'])
def get_analytics(article_id):
    """Get only analytics data for a product (faster endpoint)."""
    product = data_loader.get_product_by_id(article_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Generate sales history
    sales_history = analytics.generate_sales_history(
        article_id=article_id,
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        months=12
    )
    
    # Generate forecast
    forecast = analytics.generate_forecast(sales_history['sales'], periods=3)
    
    # Calculate metrics
    metrics = analytics.calculate_metrics(sales_history)
    
    return jsonify({
        'sales': sales_history,
        'forecast': forecast,
        'metrics': metrics
    })


@app.route('/api/segments/<int:article_id>', methods=['GET'])
def get_segments(article_id):
    """Get customer segment analysis for a product."""
    product = data_loader.get_product_by_id(article_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Analyze segments
    segments = segmentation.analyze_product_segments(
        product_name=product['prod_name'],
        product_type=product['product_type_name'],
        department=product.get('department_name', ''),
        color_group=product.get('colour_group_name', '')
    )
    
    # Generate personas
    mock_metrics = {'growth_rate': 10, 'avg_price': 50}
    personas = segmentation.generate_buyer_personas(segments, mock_metrics)
    
    return jsonify({
        'segments': segments,
        'personas': personas
    })


@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get available filter options."""
    return jsonify({
        'categories': data_loader.get_product_categories()[:50],  # Top 50
        'colors': data_loader.get_colors(),
        'departments': data_loader.get_departments()
    })


@app.route('/api/demographics', methods=['GET'])
def get_demographics():
    """Get overall customer demographics."""
    return jsonify(data_loader.get_customer_demographics())


@app.route('/api/insights', methods=['POST'])
def generate_insights():
    """Generate custom insights based on provided data."""
    data = request.json
    
    insights = llm_service.generate_insights(
        product_name=data.get('product_name', 'Product'),
        sales_data=data.get('sales_data', {}),
        forecast_data=data.get('forecast_data', {}),
        segment_data=data.get('segment_data', {})
    )
    
    return jsonify({'insights': insights})


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"\n{'='*60}")
    print(f"  ShopSight API Server")
    print(f"{'='*60}")
    print(f"  Server running at: http://localhost:{port}")
    print(f"  Frontend URL: {os.getenv('CORS_ORIGINS', 'http://localhost:3000')}")
    print(f"  Debug mode: {debug}")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
