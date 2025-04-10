import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch, Mock
import time
from interface_stats import InterfaceStats

class TestInterfaceStats(unittest.TestCase):
    @patch('psutil.net_if_stats')
    def test_get_default_interface(self, mock_if_stats):
        mock_if_stats.return_value = {
            'lo': Mock(isup=True),
            'eth0': Mock(isup=True),
            'wlan0': Mock(isup=False)
        }
        
        with patch('psutil.net_io_counters') as mock_counters:
            mock_counters.return_value = {
                'eth0': Mock(
                    bytes_sent=1000,
                    bytes_recv=2000,
                    packets_sent=10,
                    packets_recv=20
                )
            }
            stats = InterfaceStats()
            self.assertEqual(stats.interface_name, 'eth0')

    @patch('psutil.net_io_counters')
    def test_get_rates(self, mock_counters):
        
        mock_counters.return_value = {
            'eth0': Mock(
                bytes_sent=1000,
                bytes_recv=2000,
                packets_sent=10,
                packets_recv=20
            )
        }
        
        stats = InterfaceStats('eth0')
        initial_time = time.time()
        stats.last_time = initial_time
        
        mock_counters.return_value = {
            'eth0': Mock(
                bytes_sent=2000,  
                bytes_recv=4000,  
                packets_sent=15,
                packets_recv=30
            )
        }
        
        with patch('time.time') as mock_time:
            mock_time.return_value = initial_time + 1.0
            rates = stats.get_rates()
        
        self.assertEqual(rates['bytes_sent'], 1000.0)
        self.assertEqual(rates['bytes_recv'], 2000.0)
        self.assertEqual(rates['packets_sent'], 5.0) 
        self.assertEqual(rates['packets_recv'], 10.0)  

    @patch('psutil.net_io_counters')
    def test_get_totals(self, mock_counters):
        mock_counters.return_value = {
            'eth0': Mock(
                bytes_sent=1000,
                bytes_recv=2000,
                packets_sent=10,
                packets_recv=20
            )
        }
        
        stats = InterfaceStats('eth0')
        totals = stats.get_totals()
        
        self.assertEqual(totals['bytes_sent'], 1000)
        self.assertEqual(totals['bytes_recv'], 2000)
        self.assertEqual(totals['packets_sent'], 10)
        self.assertEqual(totals['packets_recv'], 20)

    @patch('psutil.net_if_stats')
    def test_no_active_interface(self, mock_if_stats):
        mock_if_stats.return_value = {
            'lo': Mock(isup=True),
            'eth0': Mock(isup=False),
            'wlan0': Mock(isup=False)
        }
        
        with self.assertRaises(RuntimeError):
            InterfaceStats()

    @patch('psutil.net_io_counters')
    def test_interface_not_found(self, mock_counters):
        mock_counters.return_value = {}
        
        with self.assertRaises(ValueError):
            InterfaceStats('nonexistent0')

if __name__ == '__main__':
    unittest.main()
