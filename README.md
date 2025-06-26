# 🥽 Open Doc-Tracer
A library for extracting and downloading PDFs from specific websites.

## 🛠️ Installation

```bash
git clone https://github.com/yasandu0505/test-scraper.git
cd test-scraper
```

## 🕹️ Usage

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

**Extract data for specific month in a year:**
```bash
python3 run_download.py --year 2023 --month 06
```

**Extract data for specific date:**
```bash
python3 run_download.py --year 2023 --month 06 --day 15
```

**Extract data with language filter for specific month:**
```bash
python3 run_download.py --year 2023 --month 03 --lang si
```

**Enable/disable logs:**
```bash
python3 run_download.py --c_logs y    # Enable logs
python3 run_download.py --c_logs n    # Disable logs
```

## 🎛️ Options

| Option | Description | Example | Default |
|--------|-------------|---------|---------|
| `--year` | Filter by year or download all | `--year 2023` or `--year all` | `all` |
| `--month` | Filter by specific month (01-12) | `--month 06` | None |
| `--day` | Filter by specific day (01-31) | `--day 15` | None |
| `--lang` | Specify language | `--lang en`, `--lang si`, `--lang ta`, `--lang all` | `all` |
| `--c_logs` | Enable/disable logs (Y/N) | `--c_logs Y` | `N` |

## 🌍 Language Codes

| Code | Language |
|------|----------|
| `en` | English |
| `si` | Sinhala |
| `ta` | Tamil |
| `all` | All languages |

## 📅 Date Filtering Examples

**Download all gazettes for 2023:**
```bash
python3 run_download.py --year 2023
```

**Download gazettes for June 2023:**
```bash
python3 run_download.py --year 2023 --month 06
```

**Download gazettes for June 15, 2023:**
```bash
python3 run_download.py --year 2023 --month 06 --day 15
```

**Download English gazettes for March 2023:**
```bash
python3 run_download.py --year 2023 --month 03 --lang en
```

**Download Sinhala gazettes for all available years:**
```bash
python3 run_download.py --year all --lang si
```

## ✨ Features

- **Resume capability**: If interrupted, run the same command again to resume downloads
- **Graceful shutdown**: Press `Ctrl+C` to stop after current downloads complete
- **Progress tracking**: Real-time download progress with statistics
- **Smart filtering**: Filter by year, month, day, and language
- **File validation**: Automatic validation of downloaded PDF files
- **Organized storage**: Files saved in structured folders: `year/month/day/gazette_id/`
- **Comprehensive logging**: Detailed logs for successful and failed downloads
- **Error handling**: Automatic retry for failed downloads with intelligent error reporting

## 📁 Output Structure

Downloads are organized as:
```
~/Desktop/gazette-archive/
├── 2023/
│   ├── 01/
│   │   ├── 15/
│   │   │   └── gazette_id/
│   │   │       ├── gazette_id_english.pdf
│   │   │       ├── gazette_id_sinhala.pdf
│   │   │       └── gazette_id_tamil.pdf
│   │   └── ...
│   └── ...
└── ...
```

## 📊 Log Files

For each year, the following log files are created:
- `[year]_archive_log.csv` - Successfully downloaded files
- `[year]_failed_log.csv` - Failed downloads with retry information
- `[year]_spider_log.txt` - Detailed operation log

## 🚨 Error Messages

- **No gazettes found**: `❌ No gazettes found for year 2023 with month 06`
- **Invalid year**: `❌ Year '2025' not found in years.json`
- **Invalid month**: `❌ Invalid month '13'. Must be between 01-12`
- **Invalid day**: `❌ Invalid day '32'. Must be between 01-31`

## 📟 Status

🚧 Under Development

---

**Thank you for using Doc-Tracer!**