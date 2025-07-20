# 🥽 Open Doc-Tracer
A library for extracting and downloading PDFs from specific websites.

## 🛠️ Installation

```bash
git clone https://github.com/yasandu0505/open-doc-tracer.git
cd open-doc-tracer
```

## 🕹️ Usage (Setup your cloud archive before start working)

**Show help:**
```bash
python3 main.py --help
```

**Extract data for specific year:**
```bash
python3 main.py --year 2023
```

**Extract data for specific year:**
```bash
python3 main.py --year 2023 --lang en
```

**Extract data for specific month in a year:**
```bash
python3 main.py --year 2023 --month 06 --lang en
```

**Extract data for specific date:**
```bash
python3 main.py --year 2023 --month 06 --day 15 --lang en
```

## 🎛️ Options

| Option | Description | Example | Default |
|--------|-------------|---------|---------|
| `--year` | Filter by year or download all | `--year 2023` | None |
| `--month` | Filter by specific month (01-12) | `--month 06` | None |
| `--day` | Filter by specific day (01-31) | `--day 15` | None |
| `--lang` | Specify language | `--lang en`, `--lang si`, `--lang ta` | None |



## 🌍 Language Codes

| Code | Language |
|------|----------|
| `en` | English |
| `si` | Sinhala |
| `ta` | Tamil |

## 📅 Date Filtering Examples

**Download all gazettes for 2023:**
```bash
python3 main.py --year 2023 --lang en
```

**Download gazettes for June 2023:**
```bash
python3 main.py --year 2023 --month 06 --lang en
```

**Download gazettes for June 15, 2023:**
```bash
python3 main.py --year 2023 --month 06 --day 15 --lang en
```

## ☁️ Setup Cloud Archive

**1.Go to Google Cloud Console**
```bash
https://console.cloud.google.com/
```

**2.Create a new project**

**3.Enable the Google Drive API in that project**

**4.Go to APIs & Services > Credentials**

**5.Click “Create Credentials” → “OAuth Client ID”**

**6.Choose Desktop App**

**7.Download the file — it's called `credentials.json`**

**8.Create a folder called `credentials` in the root of the project**

**9.Place the `credentials.json` inside the `credentials`**

**10.Look for the `config.yaml` and edit on your preference**

## ✨ Features

- **Resume capability**: If interrupted, run the same command again to resume downloads
- **Graceful shutdown**: Press `Ctrl+C` to stop after current downloads complete
- **Progress tracking**: Real-time download progress with statistics
- **Smart filtering**: Filter by year, month, day, and language
- **File validation**: Automatic validation of downloaded PDF files
- **Get new updates**: Can get new updates years and other data
- **Organized storage**: Files saved in structured folders: `year/month/day/gazette_id/`
- **Comprehensive logging**: Detailed logs for successful and failed downloads
- **Error handling**: Automatic retry for failed downloads with intelligent error reporting

## 📁 Output Structure

Downloads are organized as:
```
~/Desktop/doc-archive/
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
- `archive_logs.csv` - Successfully downloaded files
- `failed_logs.csv` - Failed downloads with retry information
- `unavailable_logs.txt` - Unavailable logs

## 🚨 Error Messages

- **No gazettes found**: `❌ No gazettes found for year 2023 with month 06`
- **Invalid year**: `❌ Year '2025' not found in years.json`
- **Invalid month**: `❌ Invalid month '13'. Must be between 01-12`
- **Invalid day**: `❌ Invalid day '32'. Must be between 01-31`

## 📟 Status

🚧 Under Development

---

**Thank you for using Doc-Tracer!**