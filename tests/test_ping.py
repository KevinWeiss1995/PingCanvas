import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch
from ping import ping

class TestPing(unittest.TestCase):

    @patch('subprocess.run')
    def test_ping_ipv4_success(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = (
            "PING 8.8.8.8 (8.8.8.8): 56 data bytes\n"
            "64 bytes from 8.8.8.8: icmp_seq=0 ttl=56 time=12.994 ms\n"
            "64 bytes from 8.8.8.8: icmp_seq=1 ttl=56 time=14.123 ms\n"
            "64 bytes from 8.8.8.8: icmp_seq=2 ttl=56 time=13.021 ms\n"
            "64 bytes from 8.8.8.8: icmp_seq=3 ttl=56 time=14.302 ms\n"
            "\n"
            "--- 8.8.8.8 ping statistics ---\n"
            "4 packets transmitted, 4 packets received, 0.0% packet loss\n"
            "round-trip min/avg/max/stddev = 12.994/13.610/14.302/0.640 ms\n"
        )
        
        result = ping("8.8.8.8")
        self.assertEqual(result, 13.610)

    @patch('subprocess.run')
    def test_ping_failure(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "ping: cannot resolve unknown.host"
        
        result = ping("unknown.host")
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_ping_ipv6_success(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = (
            "PING6 2001:4860:4860::8888(2001:4860:4860::8888) 56 data bytes\n"
            "64 bytes from 2001:4860:4860::8888: icmp_seq=1 ttl=56 time=15.6 ms\n"
            "64 bytes from 2001:4860:4860::8888: icmp_seq=2 ttl=56 time=14.8 ms\n"
            "64 bytes from 2001:4860:4860::8888: icmp_seq=3 ttl=56 time=15.2 ms\n"
            "64 bytes from 2001:4860:4860::8888: icmp_seq=4 ttl=56 time=15.4 ms\n"
            "\n"
            "--- 2001:4860:4860::8888 ping statistics ---\n"
            "4 packets transmitted, 4 received, 0% packet loss, time 3005ms\n"
            "rtt min/avg/max/mdev = 14.800/15.250/15.600/0.294 ms\n"
        )
        
        result = ping("2001:4860:4860::8888", ipv6=True)
        self.assertEqual(result, 15.250)

    def test_real_ping(self):
        """Integration test with real ping to Google's DNS"""
        result = ping("8.8.8.8", count=2)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)
        self.assertTrue(0 < result < 1000)

    def test_real_ping_verbose(self):
        """Integration test with real ping to multiple targets"""
        targets = ["8.8.8.8", "1.1.1.1"]  
        for target in targets:
            result = ping(target, count=2)
            self.assertIsNotNone(result)
            print(f"\nPing to {target}: {result}ms") 
            self.assertTrue(0 < result < 1000)

        try:
            result = ping("2001:4860:4860::8888", count=2, ipv6=True)
            if result is not None:
                print(f"\nIPv6 ping to Google DNS: {result}ms")
                self.assertTrue(0 < result < 1000)
        except:
            print("\nIPv6 not available")

if __name__ == '__main__':
    unittest.main()
