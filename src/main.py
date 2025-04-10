import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime
import time
import threading

from ping import ping
from traceroute import traceroute
from speed_measure import NetworkSpeedTest
from interface_stats import InterfaceStats
from heatmap import NetworkHeatmap

app = dash.Dash(__name__)
speed_test = NetworkSpeedTest()
interface_stats = InterfaceStats()
heatmap = NetworkHeatmap(["8.8.8.8", "1.1.1.1"])  # Google and Cloudflare DNS

network_data = {
    'timestamps': [],
    'ping_times': [],
    'download_speeds': [],
    'upload_speeds': [],
    'measured_download': 0,  # Last measured download speed
    'measured_upload': 0,    # Last measured upload speed
    'last_speed_test': 0,    # Timestamp of last speed test
    'traceroute_hops': [],
    'heatmap_data': None
}

def update_network_data():
    """Background task to update network metrics"""

    network_data['traceroute_hops'] = traceroute("8.8.8.8") or []
    
    while True:
        try:
            timestamp = datetime.now()
            
            ping_time = ping("8.8.8.8")
            interface_stats_data = interface_stats.get_rates()
            
            if not network_data['last_speed_test'] or \
               (timestamp - network_data['last_speed_test']).seconds >= 60:
                speed_results = speed_test.measure()
                network_data['measured_download'] = speed_results['download']
                network_data['measured_upload'] = speed_results['upload']
                network_data['last_speed_test'] = timestamp

            network_data['timestamps'].append(timestamp)
            network_data['ping_times'].append(ping_time)
            network_data['download_speeds'].append(network_data['measured_download'])
            network_data['upload_speeds'].append(network_data['measured_upload'])
     
            if len(network_data['timestamps']) % 10 == 0:
                heatmap.measure()
                network_data['heatmap_data'] = {
                    'z': heatmap.data.tolist(),
                    'hosts': heatmap.hosts
                }
            
            # Update traceroute every minute and store result even if empty
            if len(network_data['timestamps']) % 60 == 0:
                network_data['traceroute_hops'] = traceroute("8.8.8.8") or []
            
            if len(network_data['timestamps']) > 3600:
                for key in network_data:
                    if key not in ['traceroute_hops', 'heatmap_data', 'measured_download', 
                                 'measured_upload', 'last_speed_test']:
                        network_data[key] = network_data[key][-3600:]
            
            time.sleep(1)
        except Exception as e:
            print(f"Error in update thread: {e}")
            time.sleep(1)

threading.Thread(target=update_network_data, daemon=True).start()

app.layout = html.Div([
    html.H1('Ping Canvas', 
            style={
                'textAlign': 'center',
                'color': 'white',
                'padding': '20px'
            }),
    
    html.Div([
        html.Div([
            html.H3('Current Network Status', 
                   style={'color': 'white'}),
            html.Div(id='status-display')
        ], className='status-container'),
        
        html.Div([
            html.H3('Network Path (Traceroute)', 
                   style={'color': 'white'}),
            html.Div(id='traceroute-display')
        ], className='traceroute-container'),
        
        html.Div([
            html.H3('Network Latency (Round Trip Time)'),
            dcc.Graph(id='ping-graph')
        ], className='graph-container'),
        
        html.Div([
            html.H3('Network Speed'),
            dcc.Graph(id='speed-graph')
        ], className='graph-container'),
        
        html.Div([
            html.H3('Network Latency Heatmap'),
            dcc.Graph(id='heatmap-graph')
        ], className='graph-container')
    ]),
    
    dcc.Interval(
        id='interval-component',
        interval=1000,
        n_intervals=0
    )
], style={
    'backgroundColor': 'black',
    'minHeight': '100vh',
    'margin': 0,
    'padding': '20px'
})

def create_graph_layout(title, y_title):
    return {
        'title': {
            'text': title,
            'font': {'color': 'white'},
            'x': 0.5, 
            'xanchor': 'center'
        },
        'xaxis': {
            'title': 'Time (HH:MM:SS)',
            'gridcolor': '#333',
            'showgrid': True,
            'color': 'white',
            'title_font': {'color': 'white'}
        },
        'yaxis': {
            'title': y_title,
            'gridcolor': '#333',
            'showgrid': True,
            'color': 'white',
            'title_font': {'color': 'white'}
        },
        'paper_bgcolor': 'black',
        'plot_bgcolor': 'black',
        'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40},
        'font': {'color': 'white'},
        'legend': {
            'font': {'color': 'white'},
            'bgcolor': 'rgba(0,0,0,0)'  # Transparent background
        }
    }

def format_traceroute_hop(hop):
    """Format a single traceroute hop for display"""
    hop_num, ip, rtt = hop
    
    if ip == '*':
        return {
            'hop_num': hop_num,
            'ip': '*',
            'latency': '*'
        }

    # Parse IP and latency
    if '(' in ip:
        # Get first IP/hostname before parentheses
        main_ip = ip.split('(')[0].strip()
    else:
        main_ip = ip.strip()

    # Get best (lowest) latency
    if rtt and len(rtt) >= 2:
        try:
            latency = float(rtt[0])
            latency_str = f"{latency:.2f} {rtt[1]}"
        except ValueError:
            latency_str = '*'
    else:
        latency_str = '*'

    return {
        'hop_num': hop_num,
        'ip': main_ip,
        'latency': latency_str
    }

@app.callback(
    [Output('status-display', 'children'),
     Output('traceroute-display', 'children'),
     Output('ping-graph', 'figure'),
     Output('speed-graph', 'figure'),
     Output('heatmap-graph', 'figure')],
    Input('interval-component', 'n_intervals')
)
def update_graphs(n):

    if not network_data['timestamps']:
        current_status = html.Div([
            html.P("Collecting data...", style={'color': 'white'}),
            html.P("Please wait a few seconds", style={'color': 'white'})
        ])
        traceroute_status = html.P("Waiting for first traceroute...", 
                                  style={'color': 'white'})
        
        ping_figure = {
            'data': [],
            'layout': create_graph_layout(
                'Network Latency Over Time',
                'Ping (ms)'
            )
        }
        speed_figure = {
            'data': [],
            'layout': create_graph_layout(
                'Network Speed Over Time',
                'Speed (MB/s)'
            )
        }
        heatmap_figure = {
            'data': [],
            'layout': create_graph_layout(
                'Network Latency Heatmap',
                'Hosts'
            )
        }
        return current_status, traceroute_status, ping_figure, speed_figure, heatmap_figure

    try:
        current_status = html.Div([
            html.P(f"Current Ping: {network_data['ping_times'][-1]:.1f} ms",
                  style={'color': 'white'}),
            html.P([
                "Network Speed (measured every 5 minutes):",
                html.Br(),
                f"Download: {network_data['measured_download']:.1f} Mbps",
                html.Br(),
                f"Upload: {network_data['measured_upload']:.1f} Mbps",
                html.Br(),
                html.Span(
                    f"Last measured: {network_data['last_speed_test'].strftime('%H:%M:%S')}" 
                    if network_data['last_speed_test'] else "Not yet measured",
                    style={'fontSize': 'smaller', 'color': '#888'}
                )
            ], style={'color': 'white'})
        ])
        
        traceroute_status = html.Div([
            html.Table([
                html.Tr([
                    html.Th(col, style={'color': 'white', 'padding': '10px', 'textAlign': 'left'}) 
                    for col in ['Hop', 'IP', 'Latency']
                ]),
                *[
                    html.Tr([
                        html.Td(
                            formatted_hop['hop_num'], 
                            style={'color': 'white', 'padding': '5px', 'textAlign': 'left'}
                        ),
                        html.Td(
                            formatted_hop['ip'], 
                            style={'color': 'white', 'padding': '5px', 'textAlign': 'left'}
                        ),
                        html.Td(
                            formatted_hop['latency'], 
                            style={'color': 'white', 'padding': '5px', 'textAlign': 'left'}
                        )
                    ]) for formatted_hop in [
                        format_traceroute_hop(hop) 
                        for hop in network_data.get('traceroute_hops', [])
                    ]
                ]
            ], style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'backgroundColor': '#222',
                'borderRadius': '5px'
            }) if network_data.get('traceroute_hops') else html.P(
                "No traceroute data available", 
                style={'color': 'white'}
            )
        ])
        
        ping_figure = {
            'data': [go.Scatter(
                x=network_data['timestamps'],
                y=network_data['ping_times'],
                name='Round Trip Time',
                mode='lines+markers',
                line={'color': '#1f77b4'}
            )],
            'layout': create_graph_layout(
                'Network Latency (Ping Response Time)',
                'Latency (ms)'
            )
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
            'layout': create_graph_layout(
                'Network Speed (Measured Every Minute)',
                'Speed (Megabits per second)'
            )
        }
        
        # Heatmap figure
        if network_data.get('heatmap_data'):
            heatmap_figure = {
                'data': [go.Heatmap(
                    z=network_data['heatmap_data']['z'],
                    x=network_data['timestamps'][-len(network_data['heatmap_data']['z'][0]):],
                    y=network_data['heatmap_data']['hosts'],
                    colorscale='RdYlGn_r',
                    colorbar={'title': 'Latency (ms)'}
                )],
                'layout': create_graph_layout(
                    'Network Latency Heatmap',
                    'Hosts'
                )
            }
        else:
            heatmap_figure = {
                'data': [],
                'layout': create_graph_layout(
                    'Network Latency Heatmap',
                    'Hosts'
                )
            }
        
        return current_status, traceroute_status, ping_figure, speed_figure, heatmap_figure
    except Exception as e:
        print(f"Error updating graphs: {e}")
        return update_graphs(n)  

if __name__ == '__main__':
    app.run(debug=True)
