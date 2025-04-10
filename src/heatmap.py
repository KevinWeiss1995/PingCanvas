import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from ping import ping

class NetworkHeatmap:
    def __init__(self, hosts, interval_minutes=5, history_hours=24):
        """
        Initialize network heatmap.
        
        :param hosts: List of hosts to monitor
        :param interval_minutes: Minutes between measurements
        :param history_hours: Hours of history to maintain
        """
        self.hosts = hosts
        self.interval = interval_minutes
        self.history_hours = history_hours
        self.measurements = len(hosts)
        self.timepoints = (history_hours * 60) // interval_minutes
        self.data = np.zeros((self.measurements, self.timepoints))
        self.data.fill(np.nan)
        self.current_index = 0

    def measure(self):
        """Take a measurement of all hosts and add to data"""
        for i, host in enumerate(self.hosts):
            latency = ping(host, count=2)
            if latency is not None:
                self.data[i, self.current_index] = latency
        
        self.current_index = (self.current_index + 1) % self.timepoints

    def plot(self, filename=None):
        """
        Generate and optionally save the heatmap.
        
        :param filename: If provided, save plot to this file
        """
        plt.figure(figsize=(12, len(self.hosts) * 0.5))
      
        masked_data = np.ma.masked_invalid(self.data)
      
        plt.imshow(
            masked_data,
            aspect='auto',
            cmap='RdYlGn_r',
            interpolation='nearest'
        )
        
        plt.colorbar(label='Latency (ms)')
        
        plt.yticks(range(len(self.hosts)), self.hosts)
        plt.xlabel('Time (last {} hours)'.format(self.history_hours))
        plt.ylabel('Hosts')
        plt.title('Network Latency Heatmap')
        
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
        
        plt.close()

if __name__ == "__main__":
    hosts = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]  # Google, Cloudflare, Quad9
    heatmap = NetworkHeatmap(hosts, interval_minutes=1, history_hours=1)
    
    for _ in range(60):
        heatmap.measure()
    
    heatmap.plot()
