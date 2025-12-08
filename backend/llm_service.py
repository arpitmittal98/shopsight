"""
LLM Service Module
Handles LLM API integration (Gemini or OpenAI) for natural language understanding and insights generation.
"""
import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize LLM service with support for multiple providers.
        Priority: Gemini > Hugging Face (Llama 3.3 70B) > OpenAI > Fallback
        
        Args:
            api_key: API key for the LLM provider
            provider: 'gemini', 'huggingface', 'openai', or None (auto-detect from env)
        """
        self.provider = provider or os.getenv('LLM_PROVIDER', 'auto')
        self.client = None
        
        # If specific provider requested, try only that one
        if self.provider == 'huggingface':
            hf_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
            if hf_key and hf_key != 'your_huggingface_api_key_here':
                try:
                    import requests
                    self.hf_token = hf_key
                    self.hf_model = "meta-llama/Llama-3.1-8B-Instruct:nebius"
                    self.hf_api_url = "https://router.huggingface.co/v1/chat/completions"
                    self.client = "huggingface_chat"
                    print("✓ Hugging Face Llama 3.1 8B initialized")
                    return
                except Exception as e:
                    print(f"⚠ Hugging Face initialization failed: {e}")
        
        if self.provider == 'openai':
            openai_key = api_key or os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'your_openai_api_key_here':
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=openai_key)
                    print("✓ OpenAI API initialized")
                    return
                except Exception as e:
                    print(f"⚠ OpenAI initialization failed: {e}")
        
        if self.provider == 'gemini':
            gemini_key = api_key or os.getenv('GEMINI_API_KEY')
            if gemini_key and gemini_key != 'your_gemini_api_key_here':
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    self.client = genai.GenerativeModel('gemini-2.0-flash')
                    print("✓ Gemini 2.0 Flash initialized")
                    return
                except Exception as e:
                    print(f"⚠ Gemini initialization failed: {e}")
        
        # Auto mode: Try providers in priority order (Gemini > HF > OpenAI)
        if self.provider == 'auto':
            # Try Gemini first (best free tier)
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key and gemini_key != 'your_gemini_api_key_here':
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    self.client = genai.GenerativeModel('gemini-2.0-flash')
                    self.provider = 'gemini'
                    print("✓ Gemini 2.0 Flash initialized")
                    return
                except ImportError:
                    print("⚠ google-generativeai not installed. Run: pip install google-generativeai")
                except Exception as e:
                    print(f"⚠ Gemini initialization failed: {e}")
        
        # Try Hugging Face Llama 3.1 8B (new chat completions API)
        if self.provider == 'auto':
            hf_key = os.getenv('HUGGINGFACE_API_KEY')
            if hf_key and hf_key != 'your_huggingface_api_key_here':
                try:
                    import requests
                    # Store credentials for OpenAI-compatible chat completions API
                    self.hf_token = hf_key
                    self.hf_model = "meta-llama/Llama-3.1-8B-Instruct:nebius"
                    self.hf_api_url = "https://router.huggingface.co/v1/chat/completions"
                    self.client = "huggingface_chat"  # Using OpenAI-compatible API
                    self.provider = 'huggingface'
                    print("✓ Hugging Face Llama 3.1 8B initialized")
                    return
                except ImportError:
                    print("⚠ requests library not available")
                except Exception as e:
                    print(f"⚠ Hugging Face initialization failed: {e}")
        
            # Try OpenAI (paid)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'your_openai_api_key_here':
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=openai_key)
                    self.provider = 'openai'
                    print("✓ OpenAI API initialized")
                    return
                except Exception as e:
                    print(f"⚠ OpenAI initialization failed: {e}")
        
        # No API available - use fallback
        print(f"⚠ No LLM API configured. Using fallback mode.")
        print("  Priority: Gemini > Hugging Face > OpenAI")
        print("  To use Gemini: Set GEMINI_API_KEY in .env")
        print("  To use Hugging Face: Set HUGGINGFACE_API_KEY in .env")
        print("  To use OpenAI: Set OPENAI_API_KEY in .env")
        self.client = None
        self.provider = 'fallback'
    
    def parse_search_query(self, query: str) -> Dict:
        """
        Parse natural language query into structured search parameters.
        
        Example: "black running shoes for women" ->
        {
            'keywords': ['black', 'running', 'shoes', 'women'],
            'category': 'shoes',
            'color': 'black',
            'gender': 'women',
            'attributes': ['running']
        }
        """
        if self.client:
            try:
                prompt = f"""Parse this product search query into structured JSON.

Query: "{query}"

Extract:
- keywords: list of all important words
- category: clothing type (shoes, dress, shirt, etc.) or null
- color: color name or null
- gender: "women", "men", "unisex" or null
- attributes: style attributes like "running", "casual", "formal"

Return ONLY valid JSON with these exact keys. Do not enclose the JSON in markdown or code blocks."""

                if self.provider == 'gemini':
                    response = self.client.generate_content(prompt)
                    result_text = response.text.strip()
                    # Extract JSON from markdown code blocks if present
                    if '```json' in result_text:
                        result_text = result_text.split('```json')[1].split('```')[0].strip()
                    elif '```' in result_text:
                        result_text = result_text.split('```')[1].split('```')[0].strip()
                    
                    import json
                    result = json.loads(result_text)
                    return result
                
                elif self.provider == 'huggingface':
                    # Hugging Face Chat Completions API (OpenAI-compatible)
                    import requests
                    response = requests.post(
                        self.hf_api_url,
                        headers={"Authorization": f"Bearer {self.hf_token}"},
                        json={
                            "model": self.hf_model,
                            "messages": [
                                {"role": "system", "content": "You are a product search assistant. Return only valid JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 200,
                            "temperature": 0.3
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    result_text = response.json()["choices"][0]["message"]["content"].strip()
                    # Extract JSON from markdown code blocks if present
                    if '```json' in result_text:
                        result_text = result_text.split('```json')[1].split('```')[0].strip()
                    elif '```' in result_text:
                        result_text = result_text.split('```')[1].split('```')[0].strip()
                    
                    import json
                    result = json.loads(result_text)
                    return result
                
                elif self.provider == 'openai':
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a product search assistant. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=200
                    )
                    import json
                    result = json.loads(response.choices[0].message.content)
                    return result
            
            except Exception as e:
                error_msg = str(e)
                print(f"LLM parsing error: {error_msg}")
                
                # Retry logic for rate limit errors (429)
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    import time
                    for retry in range(2):  # 2 retries
                        wait_time = (retry + 1) * 2  # 2s, 4s
                        print(f"  Retrying in {wait_time}s... (attempt {retry + 1}/2)")
                        time.sleep(wait_time)
                        try:
                            if self.provider == 'gemini':
                                response = self.client.generate_content(prompt)
                                result_text = response.text.strip()
                                if '```json' in result_text:
                                    result_text = result_text.split('```json')[1].split('```')[0].strip()
                                elif '```' in result_text:
                                    result_text = result_text.split('```')[1].split('```')[0].strip()
                                import json
                                result = json.loads(result_text)
                                print("  ✓ Retry successful")
                                return result
                        except Exception as retry_error:
                            print(f"  Retry {retry + 1} failed: {retry_error}")
                            continue
                    print("  All retries exhausted, using fallback")
                
                return self._fallback_parse(query)
        else:
            return self._fallback_parse(query)
    
    def generate_insights(
        self,
        product_name: str,
        sales_data: Dict,
        forecast_data: Dict,
        segment_data: Dict
    ) -> str:
        """
        Generate human-readable insights from analytics data.
        """
        if self.client:
            try:
                # Format forecast values for better readability
                forecast_values = forecast_data.get('forecast', [])
                forecast_str = ', '.join([f"{int(v)} units" for v in forecast_values[:3]]) if forecast_values else 'N/A'
                
                prompt = f"""You are a senior e-commerce analytics consultant. Analyze this product's performance and provide strategic, actionable insights.

**Product:** {product_name}

**Sales Performance (Last 12 Months):**
- Total Sales: {sales_data.get('total_sales', 0):,} units
- Monthly Average: {sales_data.get('avg_monthly_sales', 0)} units
- Growth Rate: {sales_data.get('growth_rate', 0):.1f}%
- Peak Performance: {sales_data.get('peak_month', 'N/A')}
- Volatility: {sales_data.get('volatility', 0):.1f}%

**3-Month Forecast:**
- Predicted Sales: {forecast_str}
- Trend Direction: {forecast_data.get('trend', 'stable').title()} ({forecast_data.get('trend_percentage', 0):.1f}%)

**Target Audience:**
- Primary Segment: {segment_data.get('top_segment', 'N/A')} ({segment_data.get('top_segment_probability', 0):.1f}%)

Provide a structured analysis with the following sections (use markdown formatting):

## Performance Summary
[2-3 sentences on overall sales performance, key strengths/concerns]

## Key Insights
- [Insight 1: Most important finding]
- [Insight 2: Notable trend or pattern]
- [Insight 3: Risk or opportunity]

## Recommendations
1. [Immediate action item]
2. [Strategic recommendation]
3. [Marketing/inventory suggestion]

Use clear markdown formatting (##, -, 1., **bold**). Be specific, data-driven, and actionable. Keep under 200 words."""

                if self.provider == 'gemini':
                    response = self.client.generate_content(prompt)
                    return response.text.strip()
                
                elif self.provider == 'huggingface':
                    # Hugging Face Chat Completions API (OpenAI-compatible)
                    import requests
                    response = requests.post(
                        self.hf_api_url,
                        headers={"Authorization": f"Bearer {self.hf_token}"},
                        json={
                            "model": self.hf_model,
                            "messages": [
                                {"role": "system", "content": "You are a senior e-commerce analytics consultant."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 250,
                            "temperature": 0.7
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"].strip()
                
                elif self.provider == 'openai':
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an e-commerce analytics expert."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=250
                    )
                    return response.choices[0].message.content.strip()
            
            except Exception as e:
                error_msg = str(e)
                print(f"LLM insights error: {error_msg}")
                
                # Retry logic for rate limit errors (429)
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    logger.warning(f"Rate limit hit for insights generation: {product_name}")
                    import time
                    for retry in range(2):  # 2 retries
                        wait_time = (retry + 1) * 2  # 2s, 4s
                        logger.info(f"Retrying insights generation in {wait_time}s (attempt {retry + 1}/2)")
                        time.sleep(wait_time)
                        try:
                            if self.provider == 'gemini':
                                response = self.client.generate_content(prompt)
                                logger.info(f"✓ Insights retry successful on attempt {retry + 1}")
                                return response.text.strip()
                        except Exception as retry_error:
                            logger.debug(f"Retry {retry + 1} failed: {retry_error}")
                            continue
                    logger.warning("All retries exhausted, using fallback insights")
                
                return self._fallback_insights(product_name, sales_data, forecast_data, segment_data)
        else:
            return self._fallback_insights(product_name, sales_data, forecast_data, segment_data)
    
    def generate_product_summary(self, product_data: Dict, insights: str) -> str:
        """Generate a conversational summary for the product."""
        if self.client:
            try:
                prompt = f"Summarize this product in 2-3 sentences:\n{product_data.get('prod_name', '')} - {product_data.get('product_type_name', '')}\nInsights: {insights}"
                
                if self.provider == 'gemini':
                    response = self.client.generate_content(prompt)
                    return response.text.strip()
                elif self.provider == 'huggingface':
                    import requests
                    response = requests.post(
                        self.hf_api_url,
                        headers={"Authorization": f"Bearer {self.hf_token}"},
                        json={
                            "model": self.hf_model,
                            "messages": [
                                {"role": "system", "content": "You are a helpful shopping assistant."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 100,
                            "temperature": 0.7
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"].strip()
                elif self.provider == 'openai':
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful shopping assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=100
                    )
                    return response.choices[0].message.content.strip()
            except:
                return f"{product_data.get('prod_name', 'Product')} is a popular {product_data.get('product_type_name', 'item')} in the {product_data.get('department_name', 'fashion')} category."
        else:
            return f"{product_data.get('prod_name', 'Product')} is a popular {product_data.get('product_type_name', 'item')} in the {product_data.get('department_name', 'fashion')} category."
    
    def _fallback_parse(self, query: str) -> Dict:
        """Simple keyword-based parsing when LLM is unavailable."""
        query_lower = query.lower()
        
        # Extract keywords
        keywords = [word.strip() for word in query_lower.split() if len(word.strip()) > 2]
        
        # Detect category
        category_keywords = {
            'shoes': ['shoe', 'sneaker', 'boot', 'sandal'],
            'dress': ['dress', 'gown'],
            'top': ['top', 'shirt', 'blouse', 't-shirt', 'tshirt'],
            'bottom': ['pant', 'jean', 'trouser', 'short', 'skirt'],
            'jacket': ['jacket', 'coat', 'blazer'],
        }
        
        category = None
        for cat, words in category_keywords.items():
            if any(word in query_lower for word in words):
                category = cat
                break
        
        # Detect color
        colors = ['black', 'white', 'blue', 'red', 'green', 'yellow', 'pink', 'grey', 'gray', 'brown']
        color = next((c for c in colors if c in query_lower), None)
        
        # Detect gender
        gender = None
        if any(word in query_lower for word in ['women', 'woman', 'female', 'ladies', 'girl']):
            gender = 'women'
        elif any(word in query_lower for word in ['men', 'man', 'male', 'boy']):
            gender = 'men'
        
        # Detect attributes
        attributes = []
        attr_keywords = ['running', 'casual', 'formal', 'sport', 'athletic', 'training']
        attributes = [attr for attr in attr_keywords if attr in query_lower]
        
        return {
            'keywords': keywords,
            'category': category,
            'color': color,
            'gender': gender,
            'attributes': attributes
        }
    
    def _fallback_insights(
        self,
        product_name: str,
        sales_data: Dict,
        forecast_data: Dict,
        segment_data: Dict
    ) -> str:
        """Generate insights without LLM."""
        total_sales = sales_data.get('total_sales', 0)
        growth_rate = sales_data.get('growth_rate', 0)
        trend = forecast_data.get('trend', 'stable')
        top_segment = segment_data.get('top_segment', 'customers')
        segment_prob = segment_data.get('top_segment_probability', 0)
        
        insights = f"{product_name} has sold {total_sales:,} units over the past 12 months"
        
        if growth_rate > 10:
            insights += f" with strong growth of {growth_rate}%"
        elif growth_rate < -10:
            insights += f" with a decline of {abs(growth_rate)}%"
        else:
            insights += " with stable performance"
        
        insights += f". The product is {trend}"
        
        if trend == 'increasing':
            insights += " and forecast shows continued growth opportunity"
        
        insights += f". Primary customer segment is {top_segment} ({segment_prob}% of buyers), "
        
        if segment_prob > 40:
            insights += "indicating strong market fit"
        else:
            insights += "suggesting opportunity for broader market appeal"
        
        insights += "."
        
        # Add recommendations
        if growth_rate > 15:
            insights += " Consider increasing inventory to meet growing demand."
        elif growth_rate < -10:
            insights += " Recommend promotional campaigns to boost sales."
        
        return insights


if __name__ == "__main__":
    # Test the LLM service
    service = LLMService()
    
    # Test query parsing
    test_queries = [
        "black running shoes for women",
        "red summer dress",
        "men's casual jacket"
    ]
    
    print("Query Parsing Tests:")
    for query in test_queries:
        result = service.parse_search_query(query)
        print(f"\nQuery: '{query}'")
        print(f"Parsed: {result}")
    
    # Test insights generation
    mock_sales = {
        'total_sales': 8450,
        'avg_monthly_sales': 704,
        'growth_rate': 18.5,
        'peak_month': '2024-11'
    }
    mock_forecast = {
        'forecast': [750, 780, 800],
        'trend': 'increasing',
        'trend_percentage': 12.3
    }
    mock_segment = {
        'top_segment': 'Fashion Forward',
        'top_segment_probability': 45.8
    }
    
    print("\n\nInsights Generation Test:")
    insights = service.generate_insights(
        "Athletic Running Shoes",
        mock_sales,
        mock_forecast,
        mock_segment
    )
    print(insights)
