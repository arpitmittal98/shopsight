"""
Customer Segmentation Module
Generates customer insights and buyer personas (mock analysis).
"""
import numpy as np
import random
from typing import Dict, List


class CustomerSegmentation:
    def __init__(self):
        self.segments = {
            'Fashion Forward': {
                'age_range': '18-30',
                'characteristics': 'Trend-conscious, early adopters, active on social media',
                'color': '#FF6B6B'
            },
            'Classic Professional': {
                'age_range': '30-45',
                'characteristics': 'Quality-focused, timeless styles, brand loyal',
                'color': '#4ECDC4'
            },
            'Value Seeker': {
                'age_range': '25-50',
                'characteristics': 'Price-conscious, sale shoppers, practical purchases',
                'color': '#FFE66D'
            },
            'Active Lifestyle': {
                'age_range': '20-40',
                'characteristics': 'Athletic wear, comfort-focused, wellness-oriented',
                'color': '#95E1D3'
            },
            'Mature Sophisticate': {
                'age_range': '45+',
                'characteristics': 'Premium quality, refined taste, loyalty program members',
                'color': '#A8DADC'
            }
        }
    
    def analyze_product_segments(
        self,
        product_name: str,
        product_type: str,
        department: str,
        color_group: str
    ) -> Dict:
        """
        Analyze which customer segments are most likely to purchase this product.
        Returns segment distribution with probabilities.
        """
        # Seed for consistency
        seed_value = hash(product_name) % 10000
        np.random.seed(seed_value)
        
        # Base probabilities for each segment
        probabilities = self._calculate_segment_probabilities(
            product_type, department, color_group
        )
        
        # Normalize to sum to 100
        total = sum(probabilities.values())
        probabilities = {k: round((v / total) * 100, 1) for k, v in probabilities.items()}
        
        # Get top segments
        sorted_segments = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'segments': probabilities,
            'top_segment': sorted_segments[0][0],
            'top_segment_probability': sorted_segments[0][1],
            'segment_details': {
                name: {
                    'probability': prob,
                    **self.segments[name]
                }
                for name, prob in probabilities.items()
            }
        }
    
    def generate_buyer_personas(
        self,
        segment_analysis: Dict,
        sales_metrics: Dict
    ) -> List[Dict]:
        """
        Generate detailed buyer personas based on segment analysis.
        """
        personas = []
        top_segments = sorted(
            segment_analysis['segments'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for segment_name, probability in top_segments:
            if probability < 10:  # Skip segments with very low probability
                continue
            
            segment_info = self.segments[segment_name]
            persona = self._generate_persona(segment_name, segment_info, probability, sales_metrics)
            personas.append(persona)
        
        return personas
    
    def _generate_persona(
        self,
        segment_name: str,
        segment_info: Dict,
        probability: float,
        sales_metrics: Dict
    ) -> Dict:
        """Generate a single buyer persona."""
        # Generate persona details
        personas_templates = {
            'Fashion Forward': {
                'name': 'Emma',
                'occupation': 'Marketing Specialist',
                'shopping_behavior': 'Shops 2-3 times per month, follows influencers',
                'price_sensitivity': 'Medium',
                'preferred_channels': 'Online, Instagram'
            },
            'Classic Professional': {
                'name': 'Michael',
                'occupation': 'Senior Manager',
                'shopping_behavior': 'Quarterly wardrobe updates, brand loyal',
                'price_sensitivity': 'Low',
                'preferred_channels': 'In-store, website'
            },
            'Value Seeker': {
                'name': 'Sarah',
                'occupation': 'Teacher',
                'shopping_behavior': 'Waits for sales, comparison shops',
                'price_sensitivity': 'High',
                'preferred_channels': 'Online deals, clearance'
            },
            'Active Lifestyle': {
                'name': 'Alex',
                'occupation': 'Fitness Instructor',
                'shopping_behavior': 'Frequent purchases, comfort priority',
                'price_sensitivity': 'Medium',
                'preferred_channels': 'Online, mobile app'
            },
            'Mature Sophisticate': {
                'name': 'Patricia',
                'occupation': 'Executive',
                'shopping_behavior': 'Selective, quality over quantity',
                'price_sensitivity': 'Low',
                'preferred_channels': 'In-store, personal shopping'
            }
        }
        
        template = personas_templates.get(segment_name, personas_templates['Classic Professional'])
        
        return {
            'segment': segment_name,
            'probability': probability,
            'age_range': segment_info['age_range'],
            'characteristics': segment_info['characteristics'],
            'name': template['name'],
            'occupation': template['occupation'],
            'shopping_behavior': template['shopping_behavior'],
            'price_sensitivity': template['price_sensitivity'],
            'preferred_channels': template['preferred_channels'],
            'estimated_purchase_frequency': self._estimate_purchase_frequency(
                segment_name, sales_metrics
            )
        }
    
    def _calculate_segment_probabilities(
        self,
        product_type: str,
        department: str,
        color_group: str
    ) -> Dict[str, float]:
        """
        Calculate probability distribution across segments based on product attributes.
        """
        probabilities = {segment: 1.0 for segment in self.segments.keys()}
        
        product_type_lower = product_type.lower() if product_type else ""
        department_lower = department.lower() if department else ""
        color_lower = color_group.lower() if color_group else ""
        
        # Athletic/active products
        if any(word in product_type_lower for word in ['sport', 'athletic', 'training', 'run']):
            probabilities['Active Lifestyle'] *= 3.0
            probabilities['Fashion Forward'] *= 1.5
        
        # Trendy items
        if any(word in product_type_lower for word in ['crop', 'oversized', 'graphic']):
            probabilities['Fashion Forward'] *= 3.0
            probabilities['Value Seeker'] *= 1.5
        
        # Professional wear
        if any(word in product_type_lower for word in ['blazer', 'shirt', 'trouser']) or \
           'jersey' in department_lower:
            probabilities['Classic Professional'] *= 2.5
            probabilities['Mature Sophisticate'] *= 2.0
        
        # Basic/essential items
        if any(word in product_type_lower for word in ['basic', 'essential', 't-shirt', 'tank']):
            probabilities['Value Seeker'] *= 2.0
            probabilities['Active Lifestyle'] *= 1.5
        
        # Premium indicators
        if any(word in department_lower for word in ['premium', 'collection']):
            probabilities['Mature Sophisticate'] *= 2.5
            probabilities['Classic Professional'] *= 2.0
        
        # Color preferences
        if any(color in color_lower for color in ['black', 'white', 'grey', 'navy']):
            probabilities['Classic Professional'] *= 1.5
            probabilities['Mature Sophisticate'] *= 1.3
        elif any(color in color_lower for color in ['bright', 'neon', 'pink']):
            probabilities['Fashion Forward'] *= 2.0
            probabilities['Active Lifestyle'] *= 1.5
        
        return probabilities
    
    def _estimate_purchase_frequency(self, segment_name: str, sales_metrics: Dict) -> str:
        """Estimate how often this segment purchases."""
        frequencies = {
            'Fashion Forward': 'High (2-3 times/month)',
            'Classic Professional': 'Medium (Quarterly)',
            'Value Seeker': 'Medium (Monthly)',
            'Active Lifestyle': 'High (Monthly)',
            'Mature Sophisticate': 'Low (2-3 times/year)'
        }
        return frequencies.get(segment_name, 'Medium (Monthly)')


if __name__ == "__main__":
    # Test the segmentation module
    segmentation = CustomerSegmentation()
    
    # Test segment analysis
    analysis = segmentation.analyze_product_segments(
        product_name="Athletic Running Shoes",
        product_type="Sneaker",
        department="Sport",
        color_group="Black"
    )
    
    print("Segment Analysis:")
    print(f"Top Segment: {analysis['top_segment']} ({analysis['top_segment_probability']}%)")
    print("\nAll Segments:")
    for segment, prob in sorted(analysis['segments'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {segment}: {prob}%")
    
    # Test persona generation
    mock_metrics = {'growth_rate': 15.2, 'avg_price': 89.99}
    personas = segmentation.generate_buyer_personas(analysis, mock_metrics)
    
    print(f"\n\nGenerated {len(personas)} Buyer Personas:")
    for persona in personas:
        print(f"\n{persona['name']} - {persona['segment']} ({persona['probability']}%)")
        print(f"  Age: {persona['age_range']}")
        print(f"  Occupation: {persona['occupation']}")
        print(f"  Behavior: {persona['shopping_behavior']}")
