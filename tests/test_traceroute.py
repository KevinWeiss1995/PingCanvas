import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch
from traceroute import traceroute

class TestTraceroute(unittest.TestCase):

    @patch('subprocess.run')
    def test_traceroute_ipv4_success(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = (
            "traceroute to 8.8.8.8, 30 hops max\n"
            "1  192.168.1.1  1.123 ms\n"
            "2  10.0.0.1  2.456 ms\n"
            "3  8.8.8.8  3.789 ms\n"
        )
        
        expected_hops = [
            ('1', '192.168.1.1', ['1.123', 'ms']),
            ('2', '10.0.0.1', ['2.456', 'ms']),
            ('3', '8.8.8.8', ['3.789', 'ms'])
        ]
        
        result = traceroute("8.8.8.8")
        self.assertEqual(result, expected_hops)

    @patch('subprocess.run')
    def test_traceroute_failure(self, mock_subprocess):
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "traceroute: unknown host"
        
        result = traceroute("unknown.host")
        self.assertIsNone(result)

    @patch('subprocess.run')
    def test_traceroute_ipv6_success(self, mock_subprocess): 
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = (
            "traceroute to 2001:4860:4860::8888, 30 hops max\n"
            "1  2001:db8::1  1.123 ms\n"
            "2  2001:db8::2  2.456 ms\n"
            "3  2001:4860:4860::8888  3.789 ms\n"
        )
        
        expected_hops = [
            ('1', '2001:db8::1', ['1.123', 'ms']),
            ('2', '2001:db8::2', ['2.456', 'ms']),
            ('3', '2001:4860:4860::8888', ['3.789', 'ms'])
        ]
        
        result = traceroute("2001:4860:4860::8888", ipv6=True)
        self.assertEqual(result, expected_hops)

    def test_real_traceroute(self):
        """Integration test with real traceroute to Google's DNS"""
        result = traceroute("8.8.8.8")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        
        # Check format of first hop
        first_hop = result[0]
        self.assertEqual(len(first_hop), 3)  # (hop_number, ip, rtt)
        self.assertEqual(first_hop[0], '1')  # First hop should be 1
        self.assertIsInstance(first_hop[1], str)  # IP should be string
        self.assertIsInstance(first_hop[2], list)  # RTT should be list
        self.assertTrue(len(first_hop[2]) >= 1)  # Should have at least one RTT value

if __name__ == '__main__':
    unittest.main()
