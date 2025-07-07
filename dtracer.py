"""
Gazette Tracker - Main Entry Point
A clean, maintainable Scrapy project for downloading government gazettes.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.argument_parser import create_cli_parser
from src.cli.command_handler import CommandHandler
from src.config.config_loader import ConfigLoader
from src.utils.logging_utils import configure_scrapy_logging
from src.utils.validation_utils import validate_configuration


def main():
    """Main entry point for the Gazette Tracker application."""
    print("🚀 Gazette Tracker - Starting up...")
    
    # Load and validate configuration
    try:
        config_loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Parse command line arguments
    parser = create_cli_parser(config_loader)
    args = parser.parse_args()
    
    # Handle config file override
    if args.config != "config.yaml":
        try:
            config_loader = ConfigLoader(args.config)
        except Exception as e:
            print(f"❌ Failed to load configuration from {args.config}: {e}")
            sys.exit(1)
    
    # Validate configuration
    if not validate_configuration(config_loader):
        sys.exit(1)
    
    # Configure logging
    configure_scrapy_logging(config_loader, args.c_logs)
    
    # Handle commands
    try:
        command_handler = CommandHandler(config_loader)
        command_handler.execute(args)
    except KeyboardInterrupt:
        print(f"\n🛑 Operation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()