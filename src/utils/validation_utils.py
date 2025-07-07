"""
Validation Utils Module
Provides validation functions for configuration and user inputs.
"""

import sys


def validate_configuration(config_loader):
    """Validate configuration and return True if valid."""
    config_errors = config_loader.validate_config()
    if config_errors:
        print("❌ Configuration validation errors:")
        for error in config_errors:
            print(f"   • {error}")
        return False
    return True


def validate_date_inputs(month, day):
    """Validate month and day inputs."""
    if month:
        month = _validate_month(month)
    
    if day:
        day = _validate_day(day)
    
    return month, day


def _validate_month(month):
    """Validate month input."""
    try:
        month_int = int(month)
        if month_int < 1 or month_int > 12:
            print(f"\n❌ Invalid month '{month}'. Must be between 01-12.")
            sys.exit(1)
        return f"{month_int:02d}"
    except ValueError:
        print(f"\n❌ Invalid month format '{month}'. Use format: 01, 02, ..., 12.")
        sys.exit(1)


def _validate_day(day):
    """Validate day input."""
    try:
        day_int = int(day)
        if day_int < 1 or day_int > 31:
            print(f"\n❌ Invalid day '{day}'. Must be between 01-31.")
            sys.exit(1)
        return f"{day_int:02d}"
    except ValueError:
        print(f"\n❌ Invalid day format '{day}'. Use format: 01, 02, ..., 31.")
        sys.exit(1)