import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime
import time
import threading

from ping import ping
from traceroute import traceroute
from speed_test import SpeedTest
from interface_stats import InterfaceStats

app = dash.Dash(__name__)
speed_test = SpeedTest()
interface_stats = InterfaceStats()

network_data = {
    'timestamps': [],
    'ping_times': [],
    'download_speeds': [],
    'interface_speeds': []
}

def update_network_data():
    """Background task to update network metrics"""
    while True:
        timestamp = datetime.now()
     
        ping_time = ping("8.8.8.8")
        interface_stats_data = interface_stats.get_rates()
       
        network_data['timestamps'].append(timestamp)
        network_data['ping_times'].append(ping_time)
        network_data['interface_speeds'].append(interface_stats_data['bytes_recv'] / 1_000_000)  # Convert to MB/s
      
        if len(network_data['timestamps']) > 3600:
            for key in network_data:
                network_data[key] = network_data[key][-3600:]
        
        time.sleep(1)

threading.Thread(target=update_network_data, daemon=True).start()

app.layout = html.Div([
    html.H1('Network Monitor Dashboard'),
    
    html.Div([
        html.Div([
            html.H3('Current Network Status'),
            html.Div(id='status-display')
        ], className='status-container'),
        
        html.Div([
            html.H3('Network Latency'),
            dcc.Graph(id='ping-graph')
        ], className='graph-container'),
        
        html.Div([
            html.H3('Network Speed'),
            dcc.Graph(id='speed-graph')
        ], className='graph-container')
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    [Output('status-display', 'children'),
     Output('ping-graph', 'figure'),
     Output('speed-graph', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):
    current_status = html.Div([
        html.P(f"Current Ping: {network_data['ping_times'][-1]:.1f} ms"),
        html.P(f"Network Speed: {network_data['interface_speeds'][-1]:.1f} MB/s")
    ])
   
    ping_figure = {
        'data': [go.Scatter(
            x=network_data['timestamps'],
            y=network_data['ping_times'],
            name='Ping (ms)'
        )],
        'layout': {
            'title': 'Network Latency Over Time',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Ping (ms)'}
        }
    }
    
    speed_figure = {
        'data': [go.Scatter(
            x=network_data['timestamps'],
            y=network_data['interface_speeds'],
            name='Speed (MB/s)'
        )],
        'layout': {
            'title': 'Network Speed Over Time',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Speed (MB/s)'}
        }
    }
    
    return current_status, ping_figure, speed_figure

if __name__ == '__main__':
    app.run(debug=True)
