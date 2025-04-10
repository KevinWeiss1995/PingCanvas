import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch, Mock
import numpy as np
from heatmap import NetworkHeatmap

class TestNetworkHeatmap(unittest.TestCase):
    def setUp(self):
        self.hosts = ["8.8.8.8", "1.1.1.1"]
        self.heatmap = NetworkHeatmap(
            hosts=self.hosts,
            interval_minutes=1,
            history_hours=1
        )

    def test_init(self):
        """Test initialization of NetworkHeatmap"""
        self.assertEqual(self.heatmap.hosts, self.hosts)
        self.assertEqual(self.heatmap.interval, 1)
        self.assertEqual(self.heatmap.history_hours, 1)
        self.assertEqual(self.heatmap.measurements, 2)
        self.assertEqual(self.heatmap.timepoints, 60)
        self.assertEqual(self.heatmap.data.shape, (2, 60))
        self.assertTrue(np.isnan(self.heatmap.data).all())
        self.assertEqual(self.heatmap.current_index, 0)

    @patch('heatmap.ping')
    def test_measure(self, mock_ping):
        """Test measurement recording"""

        mock_ping.side_effect = [10.0, 20.0]
        
        self.heatmap.measure()
        
        self.assertEqual(mock_ping.call_count, 2)
        mock_ping.assert_any_call("8.8.8.8", count=2)
        mock_ping.assert_any_call("1.1.1.1", count=2)
        
        self.assertEqual(self.heatmap.data[0, 0], 10.0)
        self.assertEqual(self.heatmap.data[1, 0], 20.0)
        self.assertEqual(self.heatmap.current_index, 1)

    @patch('heatmap.ping')
    def test_measure_with_failure(self, mock_ping):
        """Test measurement with failed pings"""
        mock_ping.side_effect = [None, 20.0]
        
        self.heatmap.measure()
        
        self.assertTrue(np.isnan(self.heatmap.data[0, 0]))
        self.assertEqual(self.heatmap.data[1, 0], 20.0)

    @patch('matplotlib.pyplot.figure')
    @patch('matplotlib.pyplot.imshow')
    @patch('matplotlib.pyplot.colorbar')
    @patch('matplotlib.pyplot.yticks')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_plot(self, mock_close, mock_savefig, mock_title, mock_ylabel, 
                  mock_xlabel, mock_yticks, mock_colorbar, mock_imshow, mock_figure):
        """Test plot generation"""
        self.heatmap.plot(filename="test.png")
       
        mock_figure.assert_called_once()
        mock_imshow.assert_called_once()
        mock_colorbar.assert_called_once()
        mock_savefig.assert_called_once_with("test.png")
        mock_close.assert_called_once()

    def test_circular_buffer(self):
        """Test that data wraps around correctly"""
        with patch('heatmap.ping') as mock_ping:
            mock_ping.return_value = 10.0
            
            for i in range(65):
                self.heatmap.measure()
            
            self.assertEqual(self.heatmap.current_index, 5)

if __name__ == '__main__':
    unittest.main()
