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
from heatmap import NetworkHeatmap

app = dash.Dash(__name__)
speed_test = SpeedTest()
interface_stats = InterfaceStats()
heatmap = NetworkHeatmap(["8.8.8.8", "1.1.1.1"])  # Google and Cloudflare DNS

network_data = {
    'timestamps': [],
    'ping_times': [],
    'download_speeds': [],
    'upload_speeds': [],
    'traceroute_hops': [],
    'heatmap_data': None
}

def update_network_data():
    """Background task to update network metrics"""
    while True:
        try:
            timestamp = datetime.now()
          
            
            ping_time = ping("8.8.8.8")
            interface_stats_data = interface_stats.get_rates()
            download_speed = interface_stats_data.get('bytes_recv', 0)  # Already in Mbps
            upload_speed = interface_stats_data.get('bytes_sent', 0)    # Already in Mbps
       
            if len(network_data['timestamps']) % 10 == 0:
                heatmap.measure()
                network_data['heatmap_data'] = {
                    'z': heatmap.data.tolist(), 
                    'hosts': heatmap.hosts
                }
            
            if len(network_data['timestamps']) % 60 == 0:  
                hops = traceroute("8.8.8.8")
                if hops:
                    network_data['traceroute_hops'] = hops
            
            network_data['timestamps'].append(timestamp)
            network_data['ping_times'].append(ping_time)
            network_data['download_speeds'].append(download_speed)
            network_data['upload_speeds'].append(upload_speed)
          
            if len(network_data['timestamps']) > 3600:
                for key in network_data:
                    if key not in ['traceroute_hops', 'heatmap_data']:
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
    'minHeight': '100vh',  # Full viewport height
    'margin': 0,
    'padding': '20px'
})

# Update all graph layouts with dark theme
def create_graph_layout(title, y_title):
    return {
        'title': {
            'text': title,
            'font': {'color': 'white'},
            'x': 0.5,  # Center the title
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
    
    # Clean up IP display
    if ip == '*':
        ip_display = '*'
        latency_display = '*'
    else:
        # Take first valid IP address
        if '(' in ip:
            # Extract first hostname/IP pair
            parts = ip.split('(')
            ip_display = parts[0].strip()
        else:
            ip_display = ip
        
        # Take first valid RTT value
        if rtt and len(rtt) >= 2:
            latency_display = f"{rtt[0]} {rtt[1]}"
        else:
            latency_display = '*'
    
    return {
        'hop_num': hop_num,
        'ip': ip_display,
        'latency': latency_display
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
        current_stats = interface_stats.get_rates()
        download_speed = current_stats.get('bytes_recv', 0)  # Already in Mbps
        upload_speed = current_stats.get('bytes_sent', 0)    # Already in Mbps

        current_status = html.Div([
            html.P(f"Current Ping: {network_data['ping_times'][-1]:.1f} ms",
                  style={'color': 'white'}),
            html.P([
                "Network Speed:",
                html.Br(),
                f"Download: {download_speed:.1f} Mbps",
                html.Br(),
                f"Upload: {upload_speed:.1f} Mbps"
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
                'Network Speed',
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
