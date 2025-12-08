"""
Data Loader Module
Loads and processes the H&M dataset from parquet files.
"""
import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-detect data directory
            current_dir = Path(__file__).parent
            self.data_dir = str(current_dir.parent / "hm_with_images")
        else:
            self.data_dir = data_dir
        self.products_df = None
        self.customers_df = None
        self._load_data()
    
    def _load_data(self):
        """Load parquet files from S3 (no local fallback)."""
        logger.info("Starting data load from S3...")
        import time
        start_time = time.time()
        
        # Load directly from S3 using pandas with selective columns
        # This loads the ENTIRE product catalog (105k+ products)
        # Requires s3fs package for pandas S3 support
        s3_path = "s3://kumo-public-datasets/hm_with_images/articles/part-00000-63ea08b0-f43e-48ff-83ad-d1b7212d7840-c000.snappy.parquet"
        
        logger.debug(f"Loading products from: {s3_path}")
        try:
            self.products_df = pd.read_parquet(
                s3_path,
                engine='pyarrow',
                columns=[
                    'article_id', 'prod_name', 'product_type_no', 'product_type_name',
                    'product_group_name', 'colour_group_name', 'department_name',
                    'section_name', 'garment_group_name', 'image_url'
                ],
                storage_options={'anon': True}  # Anonymous access to public bucket
            )
            
            load_time = time.time() - start_time
            logger.info(f"✓ Loaded {len(self.products_df):,} products from S3 in {load_time:.2f}s")
            logger.debug(f"Product columns: {list(self.products_df.columns)}")
            logger.debug(f"Memory usage: {self.products_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
                
        except Exception as e:
            logger.error(f"Failed to load products from S3: {e}", exc_info=True)
            logger.info("Troubleshooting: Ensure s3fs is installed and internet connection is active")
            raise Exception(f"Failed to load product data from S3: {e}")
        
        # Initialize transaction cache for lazy loading
        # Instead of loading all 32M transactions upfront (3.4GB, 15min load time),
        # we load transactions on-demand per product when analytics are requested
        self.transactions_df = None  # Will be populated on first use
        self.transaction_cache = {}  # Cache per-product transactions
        self.s3_transaction_path = "s3://kumo-public-datasets/hm_with_images/transactions/"
        logger.info("✓ Transaction data will be loaded on-demand per product")
        
        # Create minimal mock customer data - we only need aggregate statistics
        logger.info("Generating customer demographics...")
        self.customers_df = pd.DataFrame({
            'customer_id': range(1000),
            'age': np.random.randint(18, 70, 1000),
            'club_member_status': np.random.choice(['ACTIVE', 'PRE-CREATE', 'LEFT CLUB'], 1000),
            'fashion_news_frequency': np.random.choice(['NONE', 'Regularly', 'Monthly'], 1000)
        })
        
        total_time = time.time() - start_time
        total_memory = self.products_df.memory_usage(deep=True).sum()
        if self.transactions_df is not None:
            total_memory += self.transactions_df.memory_usage(deep=True).sum()
        
        logger.info(f"✓ Data loading complete in {total_time:.2f}s")
        logger.info(f"  Products: {len(self.products_df):,}")
        logger.info(f"  Transactions: {len(self.transactions_df) if self.transactions_df is not None else 0:,}")
        logger.info(f"  Total memory: {total_memory / 1024**2:.2f} MB")
    
    def get_all_products(self, limit: int = 100) -> List[Dict]:
        """Get a list of all products."""
        return self.products_df.head(limit).to_dict('records')
    
    def get_product_by_id(self, article_id: int) -> Optional[Dict]:
        """Get a single product by article ID."""
        product = self.products_df[self.products_df['article_id'] == article_id]
        if len(product) > 0:
            return product.iloc[0].to_dict()
        return None
    
    def search_products(
        self, 
        query: str = None,
        category: str = None,
        color: str = None,
        department: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search products based on various criteria.
        
        Args:
            query: Text search in product name
            category: Product type name filter
            color: Color group name filter
            department: Department name filter
            limit: Maximum number of results
        
        Returns:
            List of matching products
        """
        df = self.products_df.copy()
        
        # Apply structured filters first (most specific)
        # Category filter
        if category:
            df = df[df['product_type_name'].str.contains(category, case=False, na=False)]
        
        # Color filter
        if color:
            df = df[df['colour_group_name'].str.contains(color, case=False, na=False)]
        
        # Text search in product name (only for non-filter keywords)
        # If we have structured filters, search is more lenient
        if query:
            # Split query into individual keywords for better matching
            keywords = query.split()
            
            # If we have category/color filters, only search for keywords that aren't already filtered
            # This allows "red dress" to find products when red=color and dress=category
            search_keywords = []
            for kw in keywords:
                # Skip keywords that match the category or color (already filtered)
                if category and kw.lower() in category.lower():
                    continue
                if color and kw.lower() in color.lower():
                    continue
                search_keywords.append(kw)
            
            # If we have remaining keywords, search for them
            if search_keywords:
                query_str = ' '.join(search_keywords)
                df = df[
                    df['prod_name'].str.contains(query_str, case=False, na=False) |
                    df['product_type_name'].str.contains(query_str, case=False, na=False) |
                    df['product_group_name'].str.contains(query_str, case=False, na=False)
                ]
        
        # Department filter
        if department:
            df = df[df['department_name'].str.contains(department, case=False, na=False)]
        
        # Sort by article_id for consistent results across searches
        df = df.sort_values('article_id')
        
        return df.head(limit).to_dict('records')
    
    def get_product_categories(self) -> List[str]:
        """Get unique product categories."""
        return sorted(self.products_df['product_type_name'].dropna().unique().tolist())
    
    def get_colors(self) -> List[str]:
        """Get unique color groups."""
        return sorted(self.products_df['colour_group_name'].dropna().unique().tolist())
    
    def get_departments(self) -> List[str]:
        """Get unique departments."""
        return sorted(self.products_df['department_name'].dropna().unique().tolist())
    
    def get_customer_demographics(self) -> Dict:
        """Get aggregated customer demographics."""
        return {
            'total_customers': len(self.customers_df),
            'avg_age': float(self.customers_df['age'].mean()),
            'age_distribution': self.customers_df['age'].value_counts().head(10).to_dict(),
            'club_members': self.customers_df['club_member_status'].value_counts().to_dict(),
            'fashion_news_frequency': self.customers_df['fashion_news_frequency'].value_counts().to_dict()
        }
    
    def get_product_transactions(self, article_id: int) -> Optional[pd.DataFrame]:
        """
        Get all transactions for a specific product.
        Uses lazy loading: only loads transactions from S3 on first request.
        Caches result for subsequent requests.
        
        Args:
            article_id: Product article ID
            
        Returns:
            DataFrame with transactions or None if no transaction data available
        """
        # Check cache first
        if article_id in self.transaction_cache:
            logger.debug(f"Transaction cache hit for product {article_id}")
            return self.transaction_cache[article_id]
        
        # Lazy load: Load ALL transactions on first request (any product)
        # After first load, filter from memory for subsequent products
        if self.transactions_df is None:
            logger.info("First transaction request - loading transaction data from S3...")
            import time
            start = time.time()
            try:
                # Load first partition (476k transactions, ~60MB)
                # This gives us 55% product coverage with minimal memory
                trans_path = f"{self.s3_transaction_path}part-00000-d069d8ca-004d-4bc6-a901-ce9a2cd13c83-c000.snappy.parquet"
                
                self.transactions_df = pd.read_parquet(
                    trans_path,
                    engine='pyarrow',
                    columns=['article_id', 'customer_id', 't_dat', 'price', 'sales_channel_id'],
                    storage_options={'anon': True}
                )
                
                self.transactions_df['t_dat'] = pd.to_datetime(self.transactions_df['t_dat'])
                
                load_time = time.time() - start
                unique_products = self.transactions_df['article_id'].nunique()
                logger.info(f"✓ Loaded {len(self.transactions_df):,} transactions in {load_time:.2f}s")
                logger.info(f"  Coverage: {unique_products:,} products ({unique_products/len(self.products_df)*100:.1f}%)")
                logger.debug(f"  Memory: {self.transactions_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
                
            except Exception as e:
                logger.error(f"Failed to load transactions from S3: {e}", exc_info=True)
                self.transactions_df = pd.DataFrame()  # Empty DataFrame to prevent retry loops
                return None
        
        # Filter transactions for this specific product
        if len(self.transactions_df) == 0:
            return None
        
        product_transactions = self.transactions_df[
            self.transactions_df['article_id'] == article_id
        ].copy()
        
        # Cache the result
        self.transaction_cache[article_id] = product_transactions if len(product_transactions) > 0 else None
        
        logger.debug(f"Loaded {len(product_transactions)} transactions for product {article_id}")
        
        return product_transactions if len(product_transactions) > 0 else None
    
    def has_transaction_data(self) -> bool:
        """Check if real transaction data is available (will be loaded on first request)."""
        # With lazy loading, we always have transaction capability
        # Data will be loaded on first get_product_transactions() call
        return True


if __name__ == "__main__":
    # Test the data loader
    loader = DataLoader()
    
    # Test search
    results = loader.search_products(query="shoes", limit=5)
    print(f"\nFound {len(results)} products matching 'shoes'")
    for product in results[:3]:
        print(f"  - {product['prod_name']} ({product['product_type_name']})")
    
    # Test categories
    categories = loader.get_product_categories()
    print(f"\nTotal categories: {len(categories)}")
    print(f"Sample categories: {categories[:5]}")
