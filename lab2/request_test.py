import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, List


def make_request(url: str, request_id: int) -> Tuple[int, float, bool, str]:
    start_time = time.time()
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            # read the response to ensure full request completion
            _ = response.read()
            duration = time.time() - start_time
            status = response.status
            return (request_id, duration, True, f"HTTP {status}")
    except urllib.error.HTTPError as e:
        duration = time.time() - start_time
        return (request_id, duration, False, f"HTTP {e.code} Error")
    except urllib.error.URLError as e:
        duration = time.time() - start_time
        return (request_id, duration, False, f"URL Error: {e.reason}")
    except Exception as e:
        duration = time.time() - start_time
        return (request_id, duration, False, f"Error: {str(e)}")


def run_concurrent_test(url: str, num_requests: int) -> None:
    print(f"\n{'=' * 70}")
    print(f"Testing URL: {url}")
    print(f"Number of concurrent requests: {num_requests}")
    print(f"{'=' * 70}\n")

    results: List[Tuple[int, float, bool, str]] = []

    # start timing
    overall_start = time.time()

    # use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        # submit all requests
        futures = {
            executor.submit(make_request, url, i): i
            for i in range(1, num_requests + 1)
        }

        # Collect results as they complete
        for future in as_completed(futures):
            request_id, duration, success, status = future.result()
            results.append((request_id, duration, success, status))

    overall_duration = time.time() - overall_start

    # Calculate statistics
    successful_requests = [r for r in results if r[2]]
    failed_requests = [r for r in results if not r[2]]


    # Print summary
    print(f"\n{'=' * 70}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total requests:        {num_requests}")
    print(f"Successful:            {len(successful_requests)}")
    print(f"Failed:                {len(failed_requests)}")
    print(f"Total time:            {overall_duration:.3f}s")
    print(f"{'=' * 70}\n")

def main():
    """Main entry point for the script."""
    if len(sys.argv) != 5:
        print("Usage: python3 request_test.py <ip> <port> <path> <nr_req>")
        print("\nExamples:")
        print("  python3 request_test.py localhost 8000 / 10")
        print("  python3 request_test.py 127.0.0.1 8001 /test.html 20")
        sys.exit(1)

    ip = sys.argv[1]
    port = sys.argv[2]
    path = sys.argv[3]

    try:
        num_requests = int(sys.argv[4])
        if num_requests < 1:
            raise ValueError("Number of requests must be positive")
    except ValueError as e:
        print(f"Error: Invalid number of requests: {e}")
        sys.exit(1)

    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path

    # Construct URL
    url = f"http://{ip}:{port}{path}"

    try:
        run_concurrent_test(url, num_requests)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
