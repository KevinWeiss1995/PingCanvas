import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch, Mock
from speed_test import SpeedTest

class TestSpeedTest(unittest.TestCase):
    def setUp(self):
        self.speed_test = SpeedTest(host="1.1.1.1")

    @patch('subprocess.run')
    def test_measure_rtt_success(self, mock_run):
        mock_run.return_value = Mock(
            returncode=0,
            stdout="64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=14.2 ms"
        )
        
        rtt = self.speed_test._measure_rtt(56)
        self.assertEqual(rtt, 14.2)
        
        mock_run.assert_called_with(
            ['ping', '-c', '1', '-s', '56', '1.1.1.1'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_measure_rtt_failure(self, mock_run):
        mock_run.return_value = Mock(returncode=1)
        rtt = self.speed_test._measure_rtt(56)
        self.assertEqual(rtt, 0.0)

    @patch('time.time')
    @patch('subprocess.run')
    def test_run_test_success(self, mock_run, mock_time):
        # Set up mock for successful ping responses
        mock_run.return_value = Mock(
            returncode=0,
            stdout="64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=10.0 ms"
        )

        # Set up time sequence
        start = 0.0
        end = 1.0
        mock_time.side_effect = [start, end]  # Just need start and end times
        
        with patch('time.sleep') as mock_sleep:
            results = self.speed_test.run_test(samples=2)
        
        self.assertGreater(results['bandwidth'], 0)
        self.assertEqual(results['ping'], 10.0)
        self.assertEqual(results['duration'], 1.0)
        mock_sleep.assert_called_with(0.2)

    @patch('subprocess.run')
    def test_run_test_all_failures(self, mock_run):
        mock_run.return_value = Mock(returncode=1)
        
        with patch('time.sleep'):
            results = self.speed_test.run_test()
        
        self.assertEqual(results['bandwidth'], 0.0)
        self.assertEqual(results['ping'], 0.0)

    @patch('subprocess.run')
    def test_run_test_partial_failures(self, mock_run):
    
        mock_run.side_effect = [
            Mock(returncode=0, stdout="64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=10.0 ms"),
            Mock(returncode=1),
            Mock(returncode=1),
            Mock(returncode=1)
        ]
        
        with patch('time.sleep'):
            results = self.speed_test.run_test(samples=3)
        
        self.assertEqual(results['bandwidth'], 0.0)
        self.assertEqual(results['ping'], 10.0)

if __name__ == '__main__':
    unittest.main()
