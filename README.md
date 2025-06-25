# G-Tracer

A library for extracting and downloading PDFs from specific websites.

## Installation

```bash
git clone https://github.com/yasandu0505/test-scraper.git
cd test-scraper
```

## Usage

**Show help:**
```bash
python3 run_download.py --help
```

**Extract all data:**
```bash
python3 run_download.py
```

**Extract data for specific year:**
```bash
python3 run_download.py --year 2023
```

**Extract data for specific year and language:**
```bash
python3 run_download.py --year 2023 --lang en
```

**Enable/disable logs:**
```bash
python3 run_download.py --c_logs y    # Enable logs
python3 run_download.py --c_logs n    # Disable logs
```

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `--year` | Filter by year | `--year 2023` |
| `--lang` | Specify language | `--lang en` |
| `--c_logs` | Enable/disable logs (y/n) | `--c_logs y` |

## Status

🚧 Under Development
Only works for document.gov.lk
---

**Thank you for using G-Tracer!**