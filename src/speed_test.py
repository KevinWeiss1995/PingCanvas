import speedtest
from typing import Dict, Optional
from time import time

class SpeedTest:
    def __init__(self, servers: Optional[list] = None):
        """
        Initialize speed test.
        
        :param servers: Optional list of speedtest.net server IDs
        """
        self.st = speedtest.Speedtest()
        if servers:
            self.st.get_servers(servers)
        else:
            self.st.get_best_server()

    def run_test(self) -> Dict[str, float]:
        """
        Run speed test and return results.
        
        :return: Dictionary containing download_speed, upload_speed (in Mbps), and ping (ms)
        """
        start_time = time()
        
        download_speed = self.st.download() / 1_000_000  # Convert to Mbps
        
        upload_speed = self.st.upload() / 1_000_000  # Convert to Mbps
      
        ping = self.st.results.ping
        
        return {
            'download_speed': round(download_speed, 2),
            'upload_speed': round(upload_speed, 2),
            'ping': round(ping, 2),
            'duration': round(time() - start_time, 2)
        }

    def get_server_info(self) -> Dict[str, str]:
        """
        Get information about the selected speedtest server.
        
        :return: Dictionary containing server details
        """
        server = self.st.get_best_server()
        return {
            'host': server['host'],
            'name': server['name'],
            'location': f"{server['name']}, {server['country']}",
            'latency': f"{server['latency']:.2f} ms"
        }

if __name__ == "__main__":
    st = SpeedTest()
    print("Running speed test...")
    print(f"Using server: {st.get_server_info()['location']}")
    
    results = st.run_test()
    print(f"\nDownload: {results['download_speed']:.1f} Mbps")
    print(f"Upload: {results['upload_speed']:.1f} Mbps")
    print(f"Ping: {results['ping']:.1f} ms")
    print(f"Test duration: {results['duration']:.1f} seconds")
