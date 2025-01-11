import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Union
import yaml
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fish_population.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FishPopulationAnalyzer:
    """A class to analyze and visualize fish population trends."""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the analyzer with configuration settings."""
        self.config = self._load_config(config_path)
        self.data = None
        self.processed_data = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}. Using default settings.")
            return {
                'data_dir': 'data',
                'output_dir': 'output',
                'default_species': 'FCY',
                'start_year': 1950,
                'end_year': 2020,
                'missing_value_markers': ['.', 'NA', ''],
                'plot_style': {
                    'figure_size': (12, 8),
                    'line_color': 'orange',
                    'marker': 'o',
                    'grid': True
                }
            }

    def load_data(self, file_path: str) -> None:
        """
        Load and validate the fish population dataset.
        
        Args:
            file_path (str): Path to the CSV file containing fish population data
        """
        try:
            self.data = pd.read_csv(file_path)
            logger.info(f"Successfully loaded data from {file_path}")
            self._validate_data()
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    def _validate_data(self) -> None:
        """Validate the structure and content of the loaded data."""
        required_columns = ['Country (Country)', 'ASFIS species (ASFIS species)', 
                          'FAO major fishing area (FAO major fishing area)']
        
        for col in required_columns:
            if col not in self.data.columns:
                raise ValueError(f"Required column '{col}' not found in dataset")

    def clean_data(self) -> None:
        """Clean and preprocess the data."""
        try:
            # Drop flag columns
            flag_columns = [col for col in self.data.columns if col.startswith('S')]
            self.data = self.data.drop(columns=flag_columns)
            
            # Replace missing values
            for marker in self.config['missing_value_markers']:
                self.data = self.data.replace(marker, 0)
            
            # Convert to long format
            self.processed_data = pd.melt(
                self.data,
                id_vars=["Country (Country)", "ASFIS species (ASFIS species)", 
                        "FAO major fishing area (FAO major fishing area)"],
                var_name="Year",
                value_name="Population"
            )
            
            # Clean up column names and data types
            self.processed_data.columns = ["Country", "Species", "Fishing_Area", "Year", "Population"]
            self.processed_data["Year"] = pd.to_numeric(self.processed_data["Year"], errors="coerce")
            self.processed_data["Population"] = pd.to_numeric(self.processed_data["Population"], errors="coerce")
            
            logger.info("Data cleaning completed successfully")
        except Exception as e:
            logger.error(f"Error during data cleaning: {str(e)}")
            raise

    def analyze_species(self, species: Optional[str] = None, 
                       country: Optional[str] = None,
                       start_year: Optional[int] = None,
                       end_year: Optional[int] = None) -> pd.DataFrame:
        """
        Analyze population trends for a specific species and/or country.
        
        Args:
            species (str, optional): Species code to analyze
            country (str, optional): Country to analyze
            start_year (int, optional): Start year for analysis
            end_year (int, optional): End year for analysis
            
        Returns:
            pd.DataFrame: Analyzed data
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Run clean_data() first.")
            
        filtered_data = self.processed_data.copy()
        
        # Apply filters
        if species:
            filtered_data = filtered_data[filtered_data["Species"] == species]
        if country:
            filtered_data = filtered_data[filtered_data["Country"] == country]
        if start_year:
            filtered_data = filtered_data[filtered_data["Year"] >= start_year]
        if end_year:
            filtered_data = filtered_data[filtered_data["Year"] <= end_year]
            
        # Group and aggregate data
        grouped_data = filtered_data.groupby("Year")["Population"].agg([
            'sum', 'mean', 'std', 'count'
        ]).reset_index()
        
        return grouped_data

    def plot_trends(self, analyzed_data: pd.DataFrame, 
                   species: str, 
                   output_path: Optional[str] = None,
                   show_confidence: bool = True) -> None:
        """
        Create and save visualization of population trends.
        
        Args:
            analyzed_data (pd.DataFrame): Analyzed data to plot
            species (str): Species being plotted
            output_path (str, optional): Path to save the plot
            show_confidence (bool): Whether to show confidence intervals
        """
        plt.style.use('seaborn')
        fig, ax = plt.subplots(figsize=self.config['plot_style']['figure_size'])
        
        # Plot main trend line
        ax.plot(analyzed_data["Year"], analyzed_data["sum"],
                color=self.config['plot_style']['line_color'],
                marker=self.config['plot_style']['marker'],
                label=species)
        
        # Add confidence intervals if requested
        if show_confidence and 'std' in analyzed_data.columns:
            confidence_interval = 1.96 * analyzed_data['std'] / np.sqrt(analyzed_data['count'])
            ax.fill_between(analyzed_data["Year"],
                          analyzed_data["sum"] - confidence_interval,
                          analyzed_data["sum"] + confidence_interval,
                          alpha=0.2,
                          color=self.config['plot_style']['line_color'])
        
        # Customize plot
        ax.set_title(f"Population Trends for {species}")
        ax.set_xlabel("Year")
        ax.set_ylabel("Population (Tonnes)")
        ax.grid(self.config['plot_style']['grid'])
        ax.legend()
        
        # Save plot if output path provided
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {output_path}")
        
        plt.close()

    def export_data(self, output_path: str) -> None:
        """Export processed data to CSV."""
        if self.processed_data is None:
            raise ValueError("No processed data available to export")
            
        try:
            self.processed_data.to_csv(output_path, index=False)
            logger.info(f"Data exported successfully to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise

def main():
    """Main function to run the analysis tool."""
    parser = argparse.ArgumentParser(description="Fish Population Trend Analysis Tool")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--species", help="Species code to analyze")
    parser.add_argument("--country", help="Country to analyze")
    parser.add_argument("--start-year", type=int, help="Start year for analysis")
    parser.add_argument("--end-year", type=int, help="End year for analysis")
    parser.add_argument("--output-dir", default="output", help="Directory for output files")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize analyzer
    analyzer = FishPopulationAnalyzer(args.config)
    
    try:
        # Process data
        analyzer.load_data(args.input)
        analyzer.clean_data()
        
        # Analyze data
        species = args.species or analyzer.config['default_species']
        analyzed_data = analyzer.analyze_species(
            species=species,
            country=args.country,
            start_year=args.start_year,
            end_year=args.end_year
        )
        
        # Generate outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save plot
        plot_path = output_dir / f"population_trend_{species}_{timestamp}.png"
        analyzer.plot_trends(analyzed_data, species, str(plot_path))
        
        # Export processed data
        data_path = output_dir / f"processed_data_{timestamp}.csv"
        analyzer.export_data(str(data_path))
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()