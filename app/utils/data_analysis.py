import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional

class WineDataAnalyzer:
    """
    Utility class for analyzing wine production data from VitiBrasil API.
    """
    
    @staticmethod
    def clean_quantity(quantity_str: str) -> float:
        """
        Convert string quantity to float, handling special characters.
        
        Args:
            quantity_str: String representation of quantity (e.g. "169.762.429")
            
        Returns:
            float: Cleaned quantity value
        """
        if not quantity_str or quantity_str == '-':
            return 0.0
        
        try:
            # Replace dots used as thousand separators and convert comma to dot for decimal
            cleaned = quantity_str.replace('.', '')
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def prepare_dataframe(data: List[Dict]) -> pd.DataFrame:
        """
        Convert API response data to a clean DataFrame.
        
        Args:
            data: List of dictionaries from API response
            
        Returns:
            pd.DataFrame: Cleaned DataFrame with proper types
        """
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Remove header/footer rows
        df = df[df['Produto'].notna() & (df['Produto'] != '') & 
                (df['Produto'] != 'Produto') & 
                (df['Produto'] != 'DOWNLOAD') & 
                (df['Produto'] != 'TOPO')]
        
        # Convert quantity to numeric
        df['Quantidade_Numerica'] = df['Quantidade (L.)'].apply(WineDataAnalyzer.clean_quantity)
        
        return df
    
    @staticmethod
    def get_category_totals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract main category totals from the data.
        
        Args:
            df: Prepared DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with only category totals
        """
        # Main categories are in all caps
        categories = df[df['Produto'].str.isupper()]
        
        # Exclude the 'Total' row
        categories = categories[categories['Produto'] != 'Total']
        
        return categories
    
    @staticmethod
    def compare_years(data_year1: List[Dict], data_year2: List[Dict], 
                     year1: int, year2: int) -> pd.DataFrame:
        """
        Compare production between two different years.
        
        Args:
            data_year1: Data from first year
            data_year2: Data from second year
            year1: First year
            year2: Second year
            
        Returns:
            pd.DataFrame: Comparison DataFrame
        """
        df1 = WineDataAnalyzer.prepare_dataframe(data_year1)
        df2 = WineDataAnalyzer.prepare_dataframe(data_year2)
        
        # Merge on product name
        merged = pd.merge(
            df1[['Produto', 'Quantidade_Numerica']], 
            df2[['Produto', 'Quantidade_Numerica']], 
            on='Produto', 
            how='outer',
            suffixes=(f'_{year1}', f'_{year2}')
        )
        
        # Fill NaN with 0
        merged = merged.fillna(0)
        
        # Add percent change column
        merged['Variação_Percentual'] = np.where(
            merged[f'Quantidade_Numerica_{year1}'] > 0,
            (merged[f'Quantidade_Numerica_{year2}'] - merged[f'Quantidade_Numerica_{year1}']) / 
            merged[f'Quantidade_Numerica_{year1}'] * 100,
            np.nan
        )
        
        return merged
    
    @staticmethod
    def get_top_products(df: pd.DataFrame, n: int = 10, 
                        exclude_categories: bool = True) -> pd.DataFrame:
        """
        Get top N products by quantity.
        
        Args:
            df: Prepared DataFrame
            n: Number of top products to return
            exclude_categories: Whether to exclude category totals
            
        Returns:
            pd.DataFrame: Top N products
        """
        filtered_df = df
        
        if exclude_categories:
            # Exclude rows with all uppercase product names (categories)
            filtered_df = df[~df['Produto'].str.isupper()]
            
        # Sort by quantity and get top N
        top_n = filtered_df.sort_values('Quantidade_Numerica', ascending=False).head(n)
        
        return top_n
    
    @staticmethod
    def compare_endpoints(general_data: List[Dict], wine_data: List[Dict]) -> Dict:
        """
        Compare data from general production endpoint with wine production endpoint
        to determine if they return the same data.
        
        Args:
            general_data: Data from /api/v1/production/ endpoint
            wine_data: Data from /api/v1/production/wine endpoint
            
        Returns:
            Dict: Comparison results
        """
        # Process both datasets
        df_general = WineDataAnalyzer.prepare_dataframe(general_data)
        df_wine = WineDataAnalyzer.prepare_dataframe(wine_data)
        
        # Check if the datasets have the same shape
        same_shape = df_general.shape == df_wine.shape
        
        # Check if the product lists are identical
        products_general = set(df_general['Produto'].tolist())
        products_wine = set(df_wine['Produto'].tolist())
        same_products = products_general == products_wine
        
        # Find product differences if any
        products_only_in_general = products_general - products_wine
        products_only_in_wine = products_wine - products_general
        
        # Check if quantities match for common products
        common_products = products_general.intersection(products_wine)
        quantity_comparison = {}
        diff_quantities = []
        
        for product in common_products:
            gen_qty = df_general[df_general['Produto'] == product]['Quantidade_Numerica'].values[0]
            wine_qty = df_wine[df_wine['Produto'] == product]['Quantidade_Numerica'].values[0]
            
            if gen_qty != wine_qty:
                diff_quantities.append({
                    'produto': product,
                    'quantidade_general': gen_qty,
                    'quantidade_wine': wine_qty,
                    'diferenca': gen_qty - wine_qty
                })
        
        # Determine if endpoints return the same data
        is_same_data = same_shape and same_products and len(diff_quantities) == 0
        
        return {
            'same_data': is_same_data,
            'same_shape': same_shape,
            'same_products': same_products,
            'different_quantities': diff_quantities,
            'products_only_in_general': list(products_only_in_general),
            'products_only_in_wine': list(products_only_in_wine),
            'total_products_general': len(products_general),
            'total_products_wine': len(products_wine)
        }
    
    @staticmethod
    def create_endpoint_comparison_report(result: Dict) -> str:
        """
        Create a readable report from endpoint comparison results.
        
        Args:
            result: Output from compare_endpoints method
            
        Returns:
            str: Formatted report
        """
        report = []
        report.append("## Comparação de Endpoints de Produção\n")
        
        if result['same_data']:
            report.append("✅ **Os endpoints retornam EXATAMENTE os mesmos dados.**\n")
        else:
            report.append("❌ **Os endpoints retornam dados DIFERENTES.**\n")
        
        report.append(f"- Total de produtos no endpoint geral: {result['total_products_general']}")
        report.append(f"- Total de produtos no endpoint de vinhos: {result['total_products_wine']}")
        
        if result['same_shape']:
            report.append("- Os conjuntos de dados têm o mesmo formato (mesmo número de linhas e colunas)")
        else:
            report.append("- Os conjuntos de dados têm formatos diferentes")
        
        if result['same_products']:
            report.append("- Os mesmos produtos aparecem em ambos os endpoints")
        else:
            report.append("- Os produtos diferem entre os endpoints")
            
            if result['products_only_in_general']:
                report.append("\n### Produtos apenas no endpoint geral:")
                for product in sorted(result['products_only_in_general']):
                    report.append(f"- {product}")
            
            if result['products_only_in_wine']:
                report.append("\n### Produtos apenas no endpoint de vinhos:")
                for product in sorted(result['products_only_in_wine']):
                    report.append(f"- {product}")
        
        if result['different_quantities']:
            report.append("\n### Produtos com quantidades diferentes:")
            for diff in result['different_quantities']:
                report.append(f"- **{diff['produto']}**:")
                report.append(f"  - Endpoint geral: {diff['quantidade_general']}")
                report.append(f"  - Endpoint de vinhos: {diff['quantidade_wine']}")
                report.append(f"  - Diferença: {diff['diferenca']}")
        
        return "\n".join(report)

# Example usage:
"""
from app.utils.data_analysis import WineDataAnalyzer

# Get data from API
response_data = [...]  # API response data

# Create analyzer
df = WineDataAnalyzer.prepare_dataframe(response_data)

# Get top 5 products
top_products = WineDataAnalyzer.get_top_products(df, n=5)
print(top_products)

# Fetch data from both endpoints for the same year
year = 2023
general_response = requests.get(f"http://localhost:8000/api/v1/production?year={year}")
wine_response = requests.get(f"http://localhost:8000/api/v1/production/wine?year={year}")

general_data = general_response.json()['data']
wine_data = wine_response.json()['data']

# Compare the endpoints
comparison = WineDataAnalyzer.compare_endpoints(general_data, wine_data)
report = WineDataAnalyzer.create_endpoint_comparison_report(comparison)

# Print or save report
print(report)

# If the data is mostly the same but with some inconsistencies
if not comparison['same_data'] and comparison['same_products']:
    # You might want to create visualizations of the differences
    import matplotlib.pyplot as plt
    
    # Plot quantity differences for products with discrepancies
    if comparison['different_quantities']:
        products = [d['produto'] for d in comparison['different_quantities']]
        diff_values = [d['diferenca'] for d in comparison['different_quantities']]
        
        plt.figure(figsize=(10, 6))
        plt.bar(products, diff_values)
        plt.title('Diferenças de Quantidade Entre Endpoints')
        plt.ylabel('Diferença (Geral - Vinhos)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
"""
