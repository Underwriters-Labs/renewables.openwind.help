#!/usr/bin/env python3
"""
Link checker script for Openwind Help documentation website.
Tests all links found on sidebar pages and generates a report of any broken links.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json
import sys
from collections import defaultdict
from typing import List, Any

class LinkChecker:
    def __init__(self, base_url="https://openwindhelp.com", timeout=10, verify_ssl=True):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Track results
        self.errors = []  # List of error objects
        self.pages_tested = []
        self.links_tested = set()
        self.error_summary = defaultdict(int)
        self.pages_with_404s = []
        self.link_to_pages = defaultdict(list)  # Maps each link to the pages that contain it
        
    def get_page(self, url):
        """Fetch a page and return BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            return None
    
    def get_sidebar_links(self):
        """Extract all links from the sidebar."""
        print(f"Fetching sidebar from {self.base_url}")
        soup = self.get_page(self.base_url)
        
        if not soup:
            print(f"ERROR: Could not fetch main page from {self.base_url}")
            return []
        
        sidebar = soup.find('aside', {'id': 'site-sidebar'})
        if not sidebar:
            print("ERROR: Could not find sidebar element")
            return []
        
        links = sidebar.find_all('a', href=True)
        sidebar_links = []
        
        for link in links:
            href = link.get('href')
            if href and not href.startswith('http://') and not href.startswith('https://') and not href.startswith('ftp://'):
                # Internal link
                full_url = urljoin(self.base_url, href)
                sidebar_links.append(full_url)
        
        return list(set(sidebar_links))  # Remove duplicates
    
    def test_link(self, url):
        """Test a single link and return status info."""
        try:
            # Use HEAD request first (faster), fall back to GET if that fails
            response = self.session.head(url, timeout=self.timeout, verify=self.verify_ssl, allow_redirects=True)
            status_code = response.status_code
            status_text = response.reason
        except requests.exceptions.Timeout:
            return {'status_code': None, 'error': 'Timeout', 'exception': 'Timeout'}
        except requests.exceptions.ConnectionError:
            return {'status_code': None, 'error': 'Connection Error', 'exception': 'ConnectionError'}
        except requests.exceptions.RequestException as e:
            return {'status_code': None, 'error': 'Request Error', 'exception': str(type(e).__name__)}
        
        return {'status_code': status_code, 'error': None, 'status_text': status_text}
    
    def extract_links_from_page(self, url, soup):
        """Extract all links from a page."""
        if not soup:
            return []
        
        links = soup.find_all('a', href=True)
        page_links = []
        
        for link in links:
            href = link.get('href')
            if href and not href.startswith('#') and href.strip():
                # Convert relative URLs to absolute
                if href.startswith('http://') or href.startswith('https://') or href.startswith('ftp://'):
                    page_links.append(href)
                else:
                    full_url = urljoin(self.base_url, href)
                    page_links.append(full_url)
        
        return page_links
    
    def check_all_links(self):
        """Main method: check all sidebar pages and their links."""
        sidebar_links = self.get_sidebar_links()
        
        if not sidebar_links:
            print("ERROR: No sidebar links found")
            return
        
        print(f"\nFound {len(sidebar_links)} sidebar links to check")
        print("=" * 80)
        
        all_links_to_test = set()
        
        # First pass: extract all links from all sidebar pages
        print("\n[PHASE 1] Extracting links from sidebar pages...")
        for idx, page_url in enumerate(sidebar_links, 1):
            print(f"  [{idx}/{len(sidebar_links)}] Fetching {page_url}")
            soup = self.get_page(page_url)
            
            if not soup:
                error_info = {
                    'page': page_url,
                    'link': page_url,
                    'status_code': None,
                    'error': f'Could not fetch page',
                    'type': 'page_fetch_error'
                }
                self.errors.append(error_info)
                self.error_summary['Page Fetch Error'] += 1
                continue
            
            self.pages_tested.append(page_url)
            links = self.extract_links_from_page(page_url, soup)
            all_links_to_test.update(links)
            
            # Track which pages contain which links
            for link in links:
                if page_url not in self.link_to_pages[link]:
                    self.link_to_pages[link].append(page_url)
        
        print(f"\nExtracted {len(all_links_to_test)} unique links to test")
        
        # Second pass: test all links
        print(f"\n[PHASE 2] Testing {len(all_links_to_test)} links...")
        for idx, link_url in enumerate(sorted(all_links_to_test), 1):
            print(f"  [{idx}/{len(all_links_to_test)}] Testing {link_url}", end=' ')
            result = self.test_link(link_url)
            status_code = result.get('status_code')
            error = result.get('error')
            
            # Get pages that contain this link
            originating_pages = self.link_to_pages.get(link_url, [])
            
            if error:
                print(f"❌ {error}")
                error_info = {
                    'page': originating_pages,
                    'link': link_url,
                    'error': error,
                    'status_code': status_code,
                    'type': 'error'
                }
                self.errors.append(error_info)
                self.error_summary[error] += 1
            elif status_code and status_code >= 400:
                print(f"❌ HTTP {status_code}")
                error_type = f"HTTP {status_code}"
                error_info = {
                    'page': originating_pages,
                    'link': link_url,
                    'status_code': status_code,
                    'status_text': result.get('status_text', ''),
                    'error': error_type,
                    'type': '4xx/5xx'
                }
                self.errors.append(error_info)
                self.error_summary[error_type] += 1
                
                # Track pages with 404s
                if status_code == 404:
                    for page_url in originating_pages:
                        if page_url not in self.pages_with_404s:
                            self.pages_with_404s.append(page_url)
            else:
                print(f"✓ HTTP {status_code}")
            
            self.links_tested.add(link_url)
    
    def generate_report(self, report_file="link_check_report.json"):
        """Generate a detailed report file."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'summary': {
                'total_pages_checked': len(self.pages_tested),
                'total_links_tested': len(self.links_tested),
                'total_errors': len(self.errors),
                'error_breakdown': dict(self.error_summary)
            },
            'pages_with_404s': self.pages_with_404s,
            'errors': self.errors
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return report_file

    def export_errors_to_excel(self, errors: List[Any], excel_file: str):
        """Export errors list to an Excel .xlsx file.

        Columns:
        - Broken Link
        - Originating Page(s)
        - Status Info (status code or error text)
        - Status (Broken / Fixed / In Progress) -- default to 'Broken'
        """
        try:
            from openpyxl import Workbook
        except Exception:
            print("ERROR: openpyxl is required to export to Excel. Install with: pip install openpyxl")
            return None

        wb = Workbook()
        ws = wb.active
        ws.title = "Broken Links"

        headers = ["Broken Link", "Originating Page(s)", "Status Info", "Status"]
        ws.append(headers)

        for e in errors:
            link = e.get('link')
            page = e.get('page')
            # normalize page field to a string
            if isinstance(page, list):
                page_str = " | ".join(page)
            elif page is None:
                page_str = ""
            else:
                page_str = str(page)

            # Determine status info: prefer status_code if present and a number, otherwise error text
            status_info = ""
            if e.get('status_code') is not None:
                status_info = str(e.get('status_code'))
            elif e.get('error'):
                status_info = str(e.get('error'))

            # Default tracker status
            tracker_status = e.get('tracker_status', 'Broken')

            ws.append([link, page_str, status_info, tracker_status])

        try:
            wb.save(excel_file)
            return excel_file
        except Exception as exc:
            print(f"ERROR: Could not save Excel file: {exc}")
            return None
    
    def print_summary(self):
        """Print summary to console."""
        print("\n" + "=" * 80)
        print("LINK CHECK SUMMARY")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nPages Tested: {len(self.pages_tested)}")
        print(f"Links Tested: {len(self.links_tested)}")
        print(f"Total Errors Found: {len(self.errors)}")
        
        if self.error_summary:
            print(f"\nError Breakdown:")
            for error_type, count in sorted(self.error_summary.items(), key=lambda x: -x[1]):
                print(f"  {error_type}: {count}")
        
        if self.errors:
            print(f"\n⚠️  ERRORS FOUND:")
            
            # Group errors by type
            errors_by_type = defaultdict(list)
            for error in self.errors:
                error_type = error.get('error', 'Unknown')
                errors_by_type[error_type].append(error)
            
            for error_type, error_list in sorted(errors_by_type.items()):
                print(f"\n  {error_type} ({len(error_list)} found):")
                for error in error_list[:10]:  # Show first 10 of each type
                    print(f"    - {error['link']}")
                if len(error_list) > 10:
                    print(f"    ... and {len(error_list) - 10} more")
        
        if self.pages_with_404s:
            print(f"\n🔴 PAGES WITH 404 ERRORS ({len(set(self.pages_with_404s))}):")
            for page in sorted(set(self.pages_with_404s)):
                print(f"  - {page}")
        else:
            print(f"\n✓ No 404 errors found!")
        
        print("\n" + "=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Check all links on Openwind Help documentation site'
    )
    parser.add_argument(
        '--base-url',
        default='https://openwindhelp.com',
        help='Base URL of the website (default: https://openwindhelp.com)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Timeout for each request in seconds (default: 10)'
    )
    parser.add_argument(
        '--output',
        default='link_check_report.json',
        help='Output report file (default: link_check_report.json)'
    )
    parser.add_argument(
        '--excel',
        default=None,
        help='If provided, export errors to this Excel .xlsx file'
    )
    parser.add_argument(
        '--no-verify-ssl',
        action='store_true',
        help='Disable SSL verification (not recommended)'
    )
    
    args = parser.parse_args()
    
    checker = LinkChecker(
        base_url=args.base_url,
        timeout=args.timeout,
        verify_ssl=not args.no_verify_ssl
    )
    
    try:
        checker.check_all_links()
        report_path = checker.generate_report(args.output)
        # Optionally export to Excel
        if args.excel:
            excel_path = checker.export_errors_to_excel(checker.errors, args.excel)
            if excel_path:
                print(f"Excel report saved to: {excel_path}")
        checker.print_summary()
        print(f"\nDetailed report saved to: {report_path}")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
