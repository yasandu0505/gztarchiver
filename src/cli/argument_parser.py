"""
CLI Argument Parser Module
Handles command-line argument parsing with defaults from configuration.
"""

import argparse


def create_cli_parser(config_loader):
    """Create CLI argument parser with defaults from config."""
    cli_defaults = config_loader.get_cli_defaults()
    
    parser = argparse.ArgumentParser(
        description="Download gazettes by year and language.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --year 2023 --lang en
  %(prog)s --year 2023 --month 12 --day 25
  %(prog)s --update_years
  %(prog)s --show_config
        """
    )
    
    # Date arguments
    parser.add_argument(
        "--year", 
        default=cli_defaults.get('year', 'all'), 
        help="Year to download (e.g., 2023 or 'all'). Default from config."
    )
    parser.add_argument(
        "--month", 
        default=cli_defaults.get('month'), 
        help="Month to download (e.g., 01, 12). Optional."
    )
    parser.add_argument(
        "--day", 
        default=cli_defaults.get('day'), 
        help="Day to download (e.g., 01, 31). Optional."
    )
    
    # Language argument
    parser.add_argument(
        "--lang", 
        default=cli_defaults.get('language', 'all'), 
        choices=['en', 'si', 'ta', 'all'],
        help="Language: en (English), si (Sinhala), ta (Tamil), or all. Default from config."
    )
    
    # Logging argument
    parser.add_argument(
        "--c_logs", 
        default='Y' if cli_defaults.get('enable_scrapy_logs', False) else 'N',
        choices=['Y', 'N'],
        help="Enable Scrapy logs (Y/N). Default from config."
    )
    
    # Action arguments
    parser.add_argument(
        "--update_years", 
        action="store_true", 
        help="Update years.json by scraping the website first."
    )
    
    # Config arguments
    parser.add_argument(
        "--config", 
        default="config.yaml", 
        help="Path to configuration file. Default: config.yaml"
    )
    parser.add_argument(
        "--show_config", 
        action="store_true", 
        help="Show current configuration and exit."
    )
    
    return parser