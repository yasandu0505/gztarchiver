"""
Command Handler Module
Handles the execution of different commands based on CLI arguments.
"""

import sys
from src.data.years_manager import YearsManager
from src.download.download_manager import DownloadManager
from src.utils.validation_utils import validate_date_inputs


class CommandHandler:
    """Handles command execution based on CLI arguments."""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.years_manager = YearsManager(config_loader)
        self.download_manager = DownloadManager(config_loader)
    
    def execute(self, args):
        """Execute the appropriate command based on arguments."""
        # Show configuration and exit if requested
        if args.show_config:
            self.config_loader.print_config_summary()
            return
        
        # Handle --update-years flag (only update JSON and exit)
        if args.update_years:
            self._handle_update_years()
            return
        
        # Validate date inputs
        args.month, args.day = validate_date_inputs(args.month, args.day)
        
        # Handle download operations
        self._handle_download(args)
    
    def _handle_update_years(self):
        """Handle the update years command."""
        year_data = self.years_manager.update_years_json()
        if year_data:
            print("💡 You can now run the downloader without --update-years flag.")
        else:
            print("\n❌ Failed to update years.json")
            sys.exit(1)
    
    def _handle_download(self, args):
        """Handle download operations."""
        # Ensure we have years data
        year_data = self.years_manager.get_or_fetch_years_data()
        if not year_data:
            print(f"\n❌ Failed to load or fetch year data. Cannot proceed.")
            print("💡 Try using --update-years to fetch fresh data from the website.")
            sys.exit(1)
        
        # Execute download based on arguments
        if args.year.lower() == "all":
            self._handle_download_all_years(args, year_data)
        else:
            self._handle_download_specific_year(args, year_data)
    
    def _handle_download_all_years(self, args, year_data):
        """Handle download for all years."""
        if args.month or args.day:
            print(f"\n❌ Cannot use month/day filters with --year all. Please specify a specific year.")
            sys.exit(1)
        
        print(f"\n🔄 Starting download for all available years...")
        self.download_manager.download_all_years(year_data, args.lang)
    
    def _handle_download_specific_year(self, args, year_data):
        """Handle download for a specific year."""
        year_entry = self._get_year_entry(year_data, args.year)
        if not year_entry:
            print(f"\n❌ Year '{args.year}' not found in available years.")
            sys.exit(1)
        
        # Determine download type based on arguments
        if args.month and args.day:
            self._handle_exact_date_download(args, year_entry)
        elif args.month:
            self._handle_month_download(args, year_entry)
        else:
            self._handle_year_download(args, year_entry)
    
    def _handle_exact_date_download(self, args, year_entry):
        """Handle exact date download (year + month + day)."""
        if not self.download_manager.check_data_availability(
            args.year, year_entry["link"], args.month, args.day, args.lang
        ):
            print(f"\n❌ No gazettes found for {args.year}-{args.month}-{args.day}.")
            print("💡 Try checking available dates or use a different date combination.")
            sys.exit(1)
        
        print(f"\n📅 Starting download for {args.year}-{args.month}-{args.day}...")
        self.download_manager.download_specific_date(
            args.year, year_entry["link"], args.lang, args.month, args.day
        )
    
    def _handle_month_download(self, args, year_entry):
        """Handle month download (year + month)."""
        if not self.download_manager.check_data_availability(
            args.year, year_entry["link"], args.month, None, args.lang
        ):
            # Show available dates for better user experience
            available_dates = self.download_manager.get_available_dates(
                args.year, year_entry["link"], args.lang
            )
            if available_dates:
                print("📅 Available dates in this year:")
                for date in available_dates[:10]:  # Show first 10 dates
                    print(f"   • {date.strftime('%Y-%m-%d')}")
                if len(available_dates) > 10:
                    print(f"   ... and {len(available_dates) - 10} more")
            
            print(f"\n❌ No gazettes found for {args.year}-{args.month}.")
            print("💡 Try checking available months or use a different month.")
            sys.exit(1)
        
        print(f"\n📅 Starting download for {args.year}-{args.month} (entire month)...")
        self.download_manager.download_month(
            args.year, year_entry["link"], args.lang, args.month
        )
    
    def _handle_year_download(self, args, year_entry):
        """Handle year download (year only)."""
        if not self.download_manager.check_data_availability(
            args.year, year_entry["link"], None, None, args.lang
        ):
            print(f"\n❌ No gazettes found for year {args.year}.")
            print("💡 Try checking available years or use a different year.")
            sys.exit(1)
        
        print(f"\n🔄 Starting download for year {args.year}...")
        self.download_manager.download_year(
            args.year, year_entry["link"], args.lang
        )
    
    def _get_year_entry(self, year_data, year):
        """Get year entry from year data."""
        return next((item for item in year_data if item["year"] == year), None)