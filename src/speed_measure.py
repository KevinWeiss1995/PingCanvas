import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import speedtest_cli as speedtest
import time

class NetworkSpeedTest:
    def __init__(self):
        """Initialize speed test with best server"""
        try:
            self.st = speedtest.Speedtest()
            self.st.get_best_server()
        except Exception as e:
            if __name__ == "__main__":  
                print(f"Failed to initialize speedtest: {e}")
            self.st = None
    
    def measure(self):
        """Run speed test and return results in Mbps"""
        if not self.st:
            return {'download': 0, 'upload': 0}
            
        try:
            if __name__ == "__main__":
                print("Testing download speed...")
            download_speed = self.st.download() / 1_000_000

            if __name__ == "__main__": 
                print("Testing upload speed...")
            upload_speed = self.st.upload() / 1_000_000
            
            return {
                'download': download_speed,
                'upload': upload_speed
            }
        except Exception as e:
            if __name__ == "__main__":  
                print(f"Speed test error: {e}")
            try:
                self.st = speedtest.Speedtest()
                self.st.get_best_server()
            except:
                self.st = None
            return {'download': 0, 'upload': 0}

if __name__ == "__main__":
    print("Initializing speed test...")
    speed_test = NetworkSpeedTest()
    
    print("Running speed test (this may take a minute)...")
    start_time = time.time()
    results = speed_test.measure()
    duration = time.time() - start_time
    
    print(f"\nResults:")
    print(f"Download Speed: {results['download']:.2f} Mbps")
    print(f"Upload Speed: {results['upload']:.2f} Mbps")
    print(f"Test Duration: {duration:.1f} seconds") 