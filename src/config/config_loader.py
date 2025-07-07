import yaml
import os
from pathlib import Path
import logging

class ConfigLoader:
    """Centralized configuration loader for gazette spiders"""
    
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file with fallback to defaults"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            print(f"⚠️ Config file {self.config_file} not found, using defaults")
            return self.get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"✅ Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            print(f"❌ Error loading config file {self.config_file}: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration if YAML file is not available"""
        return {
            'gazette_years_spider': {
                'name': 'gazette_years',
                'start_urls': ['https://documents.gov.lk/view/extra-gazettes/egz.html'],
                'selectors': {
                    'year_links': 'div.button-container a.btn-primary',
                    'year_text': '::text'
                },
                'output': {
                    'save_to_file': True,
                    'filename': 'years.json',
                    'sort_descending': True,
                    'encoding': 'utf-8',
                    'indent': 2
                }
            },
            'gazette_download_spider': {
                'name': 'gazette_download',
                'directories': {
                    'base_dir': '~/Desktop/gazette-archive',
                    'create_year_folders': True,
                    'create_month_folders': True,
                    'create_date_folders': True,
                    'create_gazette_folders': True
                },
                'download': {
                    'delay': 1,
                    'max_retries': 3,
                    'min_file_size': 1024,
                    'timeout': 30,
                    'concurrent_requests': 16,
                    'concurrent_requests_per_domain': 8
                },
                'language_mapping': {
                    'english': 'en',
                    'sinhala': 'si',
                    'tamil': 'ta'
                },
                'logging': {
                    'level': 'INFO',
                    'log_to_file': True,
                    'log_files': {
                        'archive': '{year}_archive_log.csv',
                        'failed': '{year}_failed_log.csv',
                        'spider': '{year}_spider_log.txt'
                    }
                },
                'selectors': {
                    'table_rows': 'table tbody tr',
                    'gazette_id': 'td:nth-child(1)::text',
                    'date': 'td:nth-child(2)::text',
                    'description': 'td:nth-child(3)::text',
                    'download_cell': 'td:nth-child(4)',
                    'pdf_buttons': 'a',
                    'button_text': 'button::text'
                }
            },
            'scrapy_settings': {
                'DOWNLOAD_DELAY': 1,
                'LOG_LEVEL': 'CRITICAL',
                'CONCURRENT_REQUESTS': 16,
                'DOWNLOAD_TIMEOUT': 30
            },
            'cli_defaults': {
                'year': 'all',
                'language': 'all',
                'enable_scrapy_logs': False
            }
        }
    
    def get_spider_config(self, spider_name):
        """Get configuration for a specific spider"""
        return self.config.get(f'{spider_name}_spider', {})
    
    def get_scrapy_settings(self):
        """Get Scrapy settings from config"""
        return self.config.get('scrapy_settings', {})
    
    def get_cli_defaults(self):
        """Get CLI default values"""
        return self.config.get('cli_defaults', {})
    
    def expand_path(self, path_str):
        """Expand user home directory and environment variables in paths"""
        if path_str:
            return str(Path(path_str).expanduser().resolve())
        return path_str
    
    def get_log_files(self, spider_config, year):
        """Get log file paths with year substitution"""
        log_files = spider_config.get('logging', {}).get('log_files', {})
        return {
            key: template.format(year=year) 
            for key, template in log_files.items()
        }
    
    def validate_config(self):
        """Validate configuration values"""
        errors = []
        
        # Validate gazette_years_spider config
        years_config = self.get_spider_config('gazette_years')
        if not years_config.get('start_urls'):
            errors.append("gazette_years_spider.start_urls is required")
        
        # Validate gazette_download_spider config
        download_config = self.get_spider_config('gazette_download')
        if not download_config.get('directories', {}).get('base_dir'):
            errors.append("gazette_download_spider.directories.base_dir is required")
        
        # Validate language mapping
        lang_mapping = download_config.get('language_mapping', {})
        required_langs = ['english', 'sinhala', 'tamil']
        for lang in required_langs:
            if lang not in lang_mapping:
                errors.append(f"Missing language mapping for '{lang}'")
        
        return errors
    
    def print_config_summary(self):
        """Print a summary of the loaded configuration"""
        print("\n📋 Configuration Summary:")
        print("=" * 50)
        
        # Years spider config
        years_config = self.get_spider_config('gazette_years')
        print(f"📅 Years Spider:")
        print(f"   • Output file: {years_config.get('output', {}).get('filename', 'years.json')}")
        print(f"   • Start URL: {years_config.get('start_urls', ['Not configured'])[0]}")
        
        # Download spider config
        download_config = self.get_spider_config('gazette_download')
        base_dir = self.expand_path(download_config.get('directories', {}).get('base_dir', ''))
        print(f"💾 Download Spider:")
        print(f"   • Base directory: {base_dir}")
        print(f"   • Download delay: {download_config.get('download', {}).get('delay', 1)}s")
        print(f"   • Max retries: {download_config.get('download', {}).get('max_retries', 3)}")
        print(f"   • Concurrent requests: {self.get_scrapy_settings().get('CONCURRENT_REQUESTS', 16)}")
        
        print("=" * 50)