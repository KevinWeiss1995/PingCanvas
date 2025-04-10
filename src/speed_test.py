import socket
import time
import statistics
from typing import Dict
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

class SpeedTest:
    def __init__(self, host: str = "1.1.1.1"):
        """
        Initialize speed test using ICMP packets.
        
        :param host: Target host (default: Cloudflare DNS)
        """
        self.host = host
        self.packet_size = 1400 

    def _measure_rtt(self, size: int = 56) -> float:
        """Measure RTT for a specific packet size"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-s', str(size), self.host],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'time=' in line:
                        return float(line.split('time=')[1].split()[0])
            return 0.0
        except Exception:
            return 0.0

    def run_test(self, samples: int = 5) -> Dict[str, float]:
        """
        Run speed test and return results.
        
        :param samples: Number of measurements to take
        :return: Dictionary containing bandwidth estimate and ping
        """
        start_time = time.time()
        
        baseline_rtt = self._measure_rtt(56)
        if baseline_rtt == 0:
            end_time = time.time()
            return {
                'bandwidth': 0.0,
                'ping': 0.0,
                'duration': round(end_time - start_time, 2)
            }
        
        rtts = []
        for _ in range(samples):
            rtt = self._measure_rtt(self.packet_size)
            if rtt > 0:
                rtts.append(rtt)
            time.sleep(0.2)

        end_time = time.time()
        
        if not rtts:
            return {
                'bandwidth': 0.0,
                'ping': round(baseline_rtt, 2),
                'duration': round(end_time - start_time, 2)
            }

        median_rtt = statistics.median(rtts)
        rtt_diff = median_rtt - baseline_rtt
        if rtt_diff <= 0:
            rtt_diff = median_rtt

        bandwidth = (self.packet_size * 8) / (rtt_diff / 1000)
        
        return {
            'bandwidth': round(bandwidth / 1_000_000, 2),
            'ping': round(baseline_rtt, 2),
            'duration': round(end_time - start_time, 2)
        }

if __name__ == "__main__":
    try:
        st = SpeedTest()
        print("Estimating bandwidth...")
        
        results = st.run_test()
        print(f"\nEstimated bandwidth: {results['bandwidth']:.1f} Mbps")
        print(f"Ping: {results['ping']:.1f} ms")
        print(f"Test duration: {results['duration']:.1f} seconds")
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
