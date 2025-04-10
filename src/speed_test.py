import requests
import time
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean

class SpeedTest:
    def __init__(self, download_url: str = "https://speed.cloudflare.com/__down"):
        """
        Initialize speed test.
        
        :param download_url: URL to use for download test
        """
        self.download_url = download_url
        self.session = requests.Session()

    def _download_chunk(self) -> float:
        """Download a chunk and return speed in Mbps"""
        try:
            start = time.time()
            response = self.session.get(self.download_url, stream=True)
            size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    size += len(chunk)
            
            duration = time.time() - start
            return (size * 8) / (1_000_000 * duration)  # Convert to Mbps
        except Exception:
            return 0.0

    def run_test(self, threads: int = 4, duration: int = 5) -> Dict[str, float]:
        """
        Run speed test and return results.
        
        :param threads: Number of concurrent downloads
        :param duration: Test duration in seconds
        :return: Dictionary containing download_speed (Mbps) and ping (ms)
        """
        start_time = time.time()
        
        # Test latency
        ping_start = time.time()
        self.session.get(self.download_url, stream=True).close()
        ping = (time.time() - ping_start) * 1000
        
        # Run fixed number of downloads
        speeds = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(self._download_chunk) for _ in range(threads)]
            for future in as_completed(futures):
                if time.time() - start_time > duration:
                    break
                try:
                    speeds.append(future.result())
                except Exception:
                    continue

        if not speeds:
            return {
                'download_speed': 0.0,
                'ping': round(ping, 2),
                'duration': round(time.time() - start_time, 2)
            }

        return {
            'download_speed': round(mean(speeds), 2),
            'ping': round(ping, 2),
            'duration': round(time.time() - start_time, 2)
        }

if __name__ == "__main__":
    try:
        st = SpeedTest()
        print("Running speed test (5 seconds)...")
        
        results = st.run_test(duration=5)
        print(f"\nDownload: {results['download_speed']:.1f} Mbps")
        print(f"Ping: {results['ping']:.1f} ms")
        print(f"Test duration: {results['duration']:.1f} seconds")
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
