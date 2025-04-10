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
    'upload_speeds': [],
    'traceroute_hops': []
}

def update_network_data():
    """Background task to update network metrics"""
    while True:
        timestamp = datetime.now()
      
        ping_time = ping("8.8.8.8")
        interface_stats_data = interface_stats.get_rates()
   
        download_speed = interface_stats_data.get('bytes_recv', 0) / 1_000_000
        upload_speed = interface_stats_data.get('bytes_sent', 0) / 1_000_000
        
        if len(network_data['timestamps']) % 60 == 0:  # Once per minute
            hops = traceroute("8.8.8.8")
            if hops:
                network_data['traceroute_hops'] = hops
        
        network_data['timestamps'].append(timestamp)
        network_data['ping_times'].append(ping_time)
        network_data['download_speeds'].append(download_speed)
        network_data['upload_speeds'].append(upload_speed)
        
        if len(network_data['timestamps']) > 3600:
            for key in network_data:
                if key != 'traceroute_hops':
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
            html.H3('Network Path (Traceroute)'),
            html.Div(id='traceroute-display')
        ], className='traceroute-container'),
        
        html.Div([
            html.H3('Network Latency (Round Trip Time)'),
            dcc.Graph(id='ping-graph')
        ], className='graph-container'),
        
        html.Div([
            html.H3('Network Speed'),
            dcc.Graph(id='speed-graph')
        ], className='graph-container')
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=1000,
        n_intervals=0
    )
])

@app.callback(
    [Output('status-display', 'children'),
     Output('traceroute-display', 'children'),
     Output('ping-graph', 'figure'),
     Output('speed-graph', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):

    if not network_data['timestamps']:
        current_status = html.Div([
            html.P("Collecting data..."),
            html.P("Please wait a few seconds")
        ])
        traceroute_status = html.P("Waiting for first traceroute...")
        
        ping_figure = {
            'data': [],
            'layout': {
                'title': 'Network Latency Over Time',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Ping (ms)'}
            }
        }
        speed_figure = {
            'data': [],
            'layout': {
                'title': 'Network Speed Over Time',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Speed (MB/s)'}
            }
        }
        return current_status, traceroute_status, ping_figure, speed_figure

    try:
        # Get current interface stats for display
        current_stats = interface_stats.get_rates()
        download_speed = current_stats.get('bytes_recv', 0) / 1_000_000  # MB/s
        upload_speed = current_stats.get('bytes_sent', 0) / 1_000_000    # MB/s

        current_status = html.Div([
            html.P(f"Current Ping: {network_data['ping_times'][-1]:.1f} ms"),
            html.P([
                "Network Speed:",
                html.Br(),
                f"Download: {download_speed:.1f} MB/s",
                html.Br(),
                f"Upload: {upload_speed:.1f} MB/s"
            ])
        ])
        
        traceroute_status = html.Div([
            html.Table([
                html.Tr([html.Th(col) for col in ['Hop', 'IP', 'Latency']]),
                *[
                    html.Tr([
                        html.Td(hop[0]),
                        html.Td(hop[1]),
                        html.Td(f"{hop[2][0]} {hop[2][1]}")
                    ]) for hop in network_data.get('traceroute_hops', [])
                ]
            ]) if network_data.get('traceroute_hops') else html.P("No traceroute data available")
        ])
        
        ping_figure = {
            'data': [go.Scatter(
                x=network_data['timestamps'],
                y=network_data['ping_times'],
                name='Round Trip Time',
                mode='lines+markers',
                line={'color': '#1f77b4'}
            )],
            'layout': {
                'title': 'Network Latency (Ping Response Time)',
                'xaxis': {
                    'title': 'Time (HH:MM:SS)',
                    'gridcolor': '#e5e5e5',
                    'showgrid': True
                },
                'yaxis': {
                    'title': 'Latency (ms)',
                    'gridcolor': '#e5e5e5',
                    'showgrid': True,
                    'rangemode': 'tozero'
                },
                'paper_bgcolor': 'white',
                'plot_bgcolor': 'white',
                'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
            }
        }
        
        speed_figure = {
            'data': [
                go.Scatter(
                    x=network_data['timestamps'],
                    y=network_data['download_speeds'],
                    name='Download',
                    mode='lines+markers',
                    line={'color': '#2ca02c'}
                ),
                go.Scatter(
                    x=network_data['timestamps'],
                    y=network_data['upload_speeds'],
                    name='Upload',
                    mode='lines+markers',
                    line={'color': '#ff7f0e'}
                )
            ],
            'layout': {
                'title': 'Network Speed',
                'xaxis': {
                    'title': 'Time (HH:MM:SS)',
                    'gridcolor': '#e5e5e5',
                    'showgrid': True
                },
                'yaxis': {
                    'title': 'Speed (Megabytes/second)',
                    'gridcolor': '#e5e5e5',
                    'showgrid': True,
                    'rangemode': 'tozero'
                },
                'paper_bgcolor': 'white',
                'plot_bgcolor': 'white',
                'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40},
                'legend': {'orientation': 'h', 'y': -0.2}
            }
        }
        
        return current_status, traceroute_status, ping_figure, speed_figure
    except Exception as e:
        print(f"Error updating graphs: {e}")
        return update_graphs(n)  

if __name__ == '__main__':
    app.run(debug=True)
