import psutil
import time
from typing import Dict, Optional

class InterfaceStats:
    def __init__(self, interface_name: str = None):
        """
        Initialize interface statistics collector.
        
        :param interface_name: Name of network interface to monitor. If None, uses default interface.
        """
        self.interface_name = interface_name or self._get_default_interface()
        self._last_stats = self._get_stats()
        self._last_time = time.time()

    def _get_default_interface(self) -> str:
        """Find the default network interface"""
        stats = psutil.net_if_stats()
        for interface, stats in stats.items():
            if stats.isup and interface != 'lo':  # Skip loopback
                return interface
        raise RuntimeError("No active network interface found")

    def _get_stats(self) -> Dict:
        """Get current network statistics"""
        counters = psutil.net_io_counters(pernic=True)
        if self.interface_name not in counters:
            raise ValueError(f"Interface {self.interface_name} not found")
        return counters[self.interface_name]

    def get_rates(self) -> Dict[str, float]:
        """
        Calculate current network rates.
        
        :return: Dictionary containing bytes_sent/s, bytes_recv/s
        """
        current_time = time.time()
        current_stats = self._get_stats()
        
        time_delta = current_time - self._last_time
        if time_delta <= 0:
            return {'bytes_sent': 0, 'bytes_recv': 0}

        bytes_sent = current_stats.bytes_sent - self._last_stats.bytes_sent
        bytes_recv = current_stats.bytes_recv - self._last_stats.bytes_recv

        self._last_stats = current_stats
        self._last_time = current_time

        # Convert to bits per second first, then to Mbps
        return {
            'bytes_sent': max(0, (bytes_sent * 8) / time_delta / 1_000_000),  # Convert to Mbps
            'bytes_recv': max(0, (bytes_recv * 8) / time_delta / 1_000_000)   # Convert to Mbps
        }

    def get_totals(self) -> Dict[str, int]:
        """
        Get total transfer statistics.
        
        :return: Dictionary containing total bytes_sent, bytes_recv, packets_sent, packets_recv
        """
        stats = self._get_stats()
        return {
            'bytes_sent': stats.bytes_sent,
            'bytes_recv': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_recv': stats.packets_recv
        }

if __name__ == "__main__":
    stats = InterfaceStats()
    print(f"Monitoring interface: {stats.interface_name}")
    
    try:
        while True:
            rates = stats.get_rates()
            print(f"\rTx: {rates['bytes_sent']:.2f} Mbps, "
                  f"Rx: {rates['bytes_recv']:.2f} Mbps", end='')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped monitoring")
