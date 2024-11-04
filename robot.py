from requests.sessions import Session
from concurrent.futures import ThreadPoolExecutor
from threading import local
import signal
import validators
import re
import datetime
import argparse
import time
import requests

class Colors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'

def logger(debug, message):
    if debug:
        formatted_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.CYAN}[{Colors.WARNING}debug{Colors.CYAN}][{Colors.ENDC}{formatted_time}{Colors.CYAN}] {Colors.ENDC}{message}")

def setup_argparse():
    parser = argparse.ArgumentParser(description="Robo Finder")
    parser.add_argument("--debug", action="store_true", default=False, help="Enable debugging mode.")
    parser.add_argument('--url', '-u', required=True, help='Specify the target URL.')
    parser.add_argument('--output', '-o', default=None, help='Output file path.')
    parser.add_argument('--threads', '-t', default=10, type=int, help='Number of threads to use.')
    parser.add_argument('-c', action="store_true", default=False, help='Concatenate paths with site URL.')
    return parser.parse_args()

def extract(response):
    """Extract directives from the robots.txt file."""
    directives = []
    regex = r"Allow:\s*\S+|Disallow:\s*\S+|Sitemap:\s*\S+"
    directive_regex = re.compile(r"(allow|disallow|user[-]?agent|sitemap|crawl-delay):[ \t]*(.*)", re.IGNORECASE)

    matches = re.findall(regex, response)
    for match in matches:
        directives_found = directive_regex.findall(match)
        directives.extend(directive[1] for directive in directives_found)

    return directives

def get_all_links(args) -> list:
    """Fetch all robots.txt URLs from the Wayback Machine."""
    logger(args.debug, "Fetching robots.txt URLs from the archive.")
    try:
        response = requests.get(f"https://web.archive.org/cdx/search/cdx?url={args.url}/robots.txt&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger(args.debug, f"Error fetching data: {e}. Exiting...")
        exit(1)

    url_list = [f"https://web.archive.org/web/{entry[0]}if_/{entry[1]}" for entry in data]

    logger(args.debug, f"Fetched {len(url_list)} robots.txt files.")
    return [url for url in url_list if url != "https://web.archive.org/web/timestampif_/original"]

thread_local = local()

def get_session() -> Session:
    """Get a thread-local session object."""
    if not hasattr(thread_local, 'session'):
        thread_local.session = requests.Session()
    return thread_local.session

def concatenate(args, results) -> list:
    """Concatenate extracted paths with the site URL."""
    concatenated = []
    for path in results:
        if not validators.url(path):
            if path.startswith("/"):
                concatenated.append(args.url + path)
            else:
                concatenated.append(f"{args.url}/{path}")
        else:
            concatenated.append(path)
    return concatenated

def fetch_files(url: str, args) -> str:  # Include args
    """Fetch the content of a robots.txt file."""
    session = get_session()
    max_retries = 3
    retry_count = 0
    response = ""

    while retry_count < max_retries:
        try:
            response = session.get(url)
            logger(args.debug, f"HTTP Request sent to {url}.")
            response.raise_for_status()
            break
        except requests.exceptions.Timeout:
            logger(args.debug, f"Timeout error for {url}. Retrying...")
        except requests.exceptions.ConnectionError:
            logger(args.debug, f"Connection error for {url}. Retrying...")
        except requests.exceptions.RequestException as e:
            logger(args.debug, f"Request error: {e}. Retrying...")
        
        time.sleep(1)  # Wait before retrying
        retry_count += 1

    return response.text if response else ""

def handle_sigint(signal_number, stack_frame):
    """Handle keyboard interrupt (Ctrl+C)."""
    print("Keyboard interrupt detected, stopping processing.")
    raise KeyboardInterrupt()

def start_process(urls, args) -> list:
    """Start processing by sending HTTP requests to fetch all robots.txt files."""
    signal.signal(signal.SIGINT, handle_sigint)
    responses = []
    logger(args.debug, "Fetching robots.txt files from multiple URLs.")

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for resp in executor.map(lambda url: fetch_files(url, args), urls):  # Pass args
            if resp:
                responses.append(resp)

    return responses

def main():
    args = setup_argparse()
    start_time = time.time()
    logger(args.debug, "Starting the program.")

    url_list = get_all_links(args)
    responses = start_process(url_list, args)

    logger(args.debug, "Extracting paths from robots.txt files.")
    results = []
    for resp in responses:
        results.extend(extract(resp))

    results = list(set(results))  # Remove duplicates
    if not results:
        logger(args.debug, "No paths found. Exiting...")
        exit(1)

    if args.c:
        logger(args.debug, "Concatenating paths with the site URL.")
        results = concatenate(args, results)

    logger(args.debug, f"Total paths found: {len(results)}.")

    if args.output:
        logger(args.debug, f"Writing output to {args.output}.")
        with open(args.output, 'w') as f:
            f.writelines(f"{path}\n" for path in results)
        logger(args.debug, "Output written successfully.")

    for path in results:
        print(path)

if __name__ == "__main__":
    main()
