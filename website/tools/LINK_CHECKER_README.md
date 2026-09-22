# Link Checker for Openwind Help

This tool checks all links on the Openwind Help documentation website (openwindhelp.com) and generates a report of any broken links or HTTP errors.

## Features

- **Extracts all sidebar links** from the main page
- **Fetches each sidebar page** and extracts all links (internal and external)
- **Tests every link** with HTTP requests
- **Generates a JSON report** with detailed error information
- **Prints a console summary** with:
  - Total pages and links tested
  - Error count and breakdown by type
  - List of pages with 404 errors
  - Sample broken links by error type

## Requirements

- Python 3.6+
- `requests` library
- `beautifulsoup4` library

## Installation

Install dependencies:

```bash
pip install requests beautifulsoup4
```

Or on Windows:

```powershell
pip install requests beautifulsoup4
```

## Usage

### Basic Usage (Python)

```bash
python check_links.py
```

Or on Windows:

```powershell
python .\check_links.py
```

### Using the Bash Wrapper

```bash
bash check_links.sh
```

### With Custom URL

If the website URL has changed:

```bash
python check_links.py --base-url https://newurl.com
```

### With Custom Timeout

To increase timeout for slower connections:

```bash
python check_links.py --timeout 15
```

### With Custom Output Filename

```bash
python check_links.py --output my_report.json
```

### Disable SSL Verification (Not Recommended)

```bash
python check_links.py --no-verify-ssl
```

### See All Options

```bash
python check_links.py --help
```

## Output

The script produces two outputs:

### 1. Console Output

A human-readable summary showing:
- Pages and links tested count
- Error breakdown by type
- Specific pages with 404 errors
- Sample of broken links

Example:
```
================================================================================
LINK CHECK SUMMARY
================================================================================
Base URL: https://openwindhelp.com
Timestamp: 2025-02-10 14:30:45

Pages Tested: 45
Links Tested: 312
Total Errors Found: 8

Error Breakdown:
  HTTP 404: 5
  Connection Error: 2
  Timeout: 1

🔴 PAGES WITH 404 ERRORS (3):
  - https://openwindhelp.com/some-page
  - https://openwindhelp.com/another-page
```

### 2. JSON Report File

A detailed `link_check_report.json` file containing:
- Timestamp of the check
- Base URL used
- Summary statistics
- List of pages with 404s
- Complete list of all errors with details

Example structure:
```json
{
  "timestamp": "2025-02-10T14:30:45.123456",
  "base_url": "https://openwindhelp.com",
  "summary": {
    "total_pages_checked": 45,
    "total_links_tested": 312,
    "total_errors": 8,
    "error_breakdown": {
      "HTTP 404": 5,
      "Connection Error": 2,
      "Timeout": 1
    }
  },
  "pages_with_404s": [
    "https://openwindhelp.com/some-page"
  ],
  "errors": [
    {
      "link": "https://example.com/broken",
      "status_code": 404,
      "status_text": "Not Found",
      "error": "HTTP 404",
      "type": "4xx/5xx"
    }
  ]
}
```

## Error Types

The script categorizes errors as:

- **HTTP 404** - Page not found
- **HTTP 5xx** - Server errors
- **HTTP 4xx** - Client errors (other than 404)
- **Timeout** - Request took too long to respond
- **Connection Error** - Could not establish connection
- **Request Error** - Other HTTP request errors
- **Page Fetch Error** - Could not fetch a sidebar page

## Interpreting Results

### If you see 404s:
These are broken links on the documentation pages that should be fixed. Check the `pages_with_404s` section to see which pages contain these broken links.

### If you see Connection Errors:
These could be temporary network issues or the domain may no longer exist. Re-run the script to confirm.

### If you see Timeouts:
The remote server is slow to respond. You might need to increase the `--timeout` value.

## Notes

- The script uses `HEAD` requests for speed (only downloads headers, not page content)
- Redirects are followed automatically
- The script respects the base URL and can be used with different URLs if the documentation is moved
- External links (http, https, ftp) are fully tested
- Fragments (#anchor) are skipped as they cannot be validated by HTTP requests

## Troubleshooting

### "No sidebar links found"
This usually means the website structure has changed. Check if the CSS selector for the sidebar (`aside#site-sidebar`) still exists.

### SSL verification errors
Try adding `--no-verify-ssl` flag, but this is not recommended for production use.

### Slow performance
- Increase the `--timeout` value
- Run during off-peak hours
- Check your internet connection

## Example: Scheduled Checks

You can schedule regular checks using cron (Linux/Mac):

```bash
# Run daily at 2 AM
0 2 * * * /path/to/check_links.sh
```

Or Windows Task Scheduler for the Python script.
