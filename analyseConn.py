import sqlite3
import logging
from datetime import datetime
from dash import dcc, html, Dash, Input, Output, dash_table, callback_context, State
from dash.exceptions import PreventUpdate
import pandas as pd
import threading
import time
import socket
import psutil
from ipwhois import IPWhois

# --- Configuration du logging ---
logging.basicConfig(
    level=logging.INFO,
    #level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('connexions.log'),
        logging.StreamHandler()
    ]
)
dns_cache = {}
TOP_N = 20

def compute_agg(df, field, metric):
    """Return a DataFrame with columns [field, 'connection_count'] containing the selected aggregation metric."""
    if df is None or df.empty:
        return pd.DataFrame(columns=[field, 'connection_count'])
    # default: count rows per field
    if metric == 'sum_connection_count' and 'connection_count' in df.columns:
        agg = df.groupby(field)['connection_count'].sum().reset_index()
    elif metric == 'unique_remote_ip' and 'remote_ip' in df.columns:
        agg = df.groupby(field)['remote_ip'].nunique().reset_index(name='connection_count')
    else:
        # 'count' or fallback
        agg = df.groupby(field).size().reset_index(name='connection_count')
    return agg

# --- Data detection ---
def get_active_connections():
    logging.debug("get active connections using psutil")
    connections = []
    for conn in psutil.net_connections():
        if conn.status == 'ESTABLISHED':
            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A'
            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A'
            remote_ip = conn.raddr.ip if conn.raddr else 'N/A'
            if remote_ip != 'N/A':
                resolve_dns(remote_ip)
            connections.append({
                'local_address': local_addr,
                'remote_address': remote_addr,
                'remote_ip': remote_ip,
                'remote_port': conn.raddr.port if conn.raddr else 'N/A',
                'state': conn.status,
                'pid': conn.pid,
                'timestamp': datetime.now().isoformat()
            })
    return connections


def resolve_dns(ip):
    # Use cache first
    if ip in dns_cache:
        logging.debug(f"  {ip} with cache")
        return True
    res = {}
    try:
        logging.info(f"get dns for {ip} without cache")
        dm_info =  IPWhois(ip)
        res=dm_info.lookup_whois()
    except:
        logging.error(f"   lookup_whois info error for {ip}")
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except:
        logging.error(f"   gethostbyaddr info error for {ip}")
        hostname = 'N/A'
    desc = res["nets"][0]['description'] if 'nets' in res.keys() else ''
    creadate = res["nets"][0]['created'] if 'nets' in res.keys()  else ''
    contry = res["nets"][0]['country']   if 'nets' in res.keys()  else ''
    logging.debug(f"   DNS info    : {ip} -> {hostname} ({desc} {creadate} {contry})")
    update_resolution(ip, hostname, desc, creadate, contry)
    return True

def load_cache(db_path='connexions.db'):
    global dns_cache
    logging.debug("Load DNS cache from database")
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute('SELECT remote_ip, hostname FROM dns_resolution')
    rows = cursor.fetchall()
    dns_cache = {row[0]: row[1] for row in rows}
    conn.close()
    logging.info(f"DNS cache loaded with {len(dns_cache)} entries")
    
def update_resolution(ip, hostname, desc='', creadate='', contry='', db_path='connexions.db'):
    global dns_cache
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO dns_resolution (remote_ip, hostname, desc, contry, creadate, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(remote_ip)
        DO UPDATE SET
            hostname = excluded.hostname,
            desc = excluded.desc,
            contry = excluded.contry,
            creadate = excluded.creadate,
            timestamp = excluded.timestamp
    ''', (ip, hostname, desc, contry, creadate, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    dns_cache[ip] = hostname
    logging.debug(f"DNS updated for {ip} -> {hostname}")


def init_db(db_path='connexions.db'):
    logging.info("Init db...")
    conn = sqlite3.connect(db_path, timeout=10)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_address TEXT,
            remote_address TEXT,
            remote_ip TEXT,
            remote_port INTEGER,
            state TEXT,
            pname TEXT,
            pid INTEGER,
            connection_count INTEGER DEFAULT 1,
            last_seen TEXT,
            timestamp TEXT,
            UNIQUE(remote_ip, remote_port)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dns_resolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remote_ip TEXT UNIQUE,
            hostname TEXT,
            desc TEXT,
            contry TEXT,
            creadate TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_remote_ip_port ON active_connections(remote_ip, remote_port)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_remote_ip ON dns_resolution(remote_ip)')
    conn.commit()
    load_cache(db_path)
    conn.close()
    logging.info("Database initiated.")

def update_connections_db(db_path='connexions.db'):
    connections = get_active_connections()
    logging.info("Update db...")
    conn = sqlite3.connect(db_path, timeout=20)
    cursor = conn.cursor()
    for conn_info in connections:
        try:
            process = psutil.Process(conn_info['pid'])
            conn_info['pname'] = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
            logging.error(f"Process not found for PID {conn_info['pid']}")
            conn_info['pname'] = 'N/A'
        cursor.execute('''
            INSERT INTO active_connections (
                local_address, remote_address, remote_ip, remote_port, state, pname, pid, connection_count, last_seen, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(remote_ip, remote_port)
            DO UPDATE SET
                connection_count = connection_count + 1,
                last_seen = excluded.last_seen,
                timestamp = excluded.timestamp
        ''', (
            conn_info['local_address'],
            conn_info['remote_address'],
            conn_info['remote_ip'],
            conn_info['remote_port'],
            conn_info['state'],
            conn_info['pname'],
            conn_info['pid'],
            conn_info['timestamp'],
            conn_info['timestamp']
        ))
    conn.commit()
    conn.close()
    logging.info("Database upserted")

def get_connections_data(db_path='connexions.db'):
    df=pd.DataFrame()    
    uri = f'file:{db_path}?mode=ro'
    logging.debug("Get data from database")
    try:
        conn = sqlite3.connect(uri, timeout=20, uri=True)
        df = pd.read_sql_query("""
        SELECT
            c.remote_ip,
            c.remote_port,
            c.pname,
            c.connection_count,
            c.last_seen,
            d.hostname,
            substr(d.desc, 1, 30) as desc,
            d.contry,
            d.creadate
        FROM
            active_connections c
        LEFT JOIN
            dns_resolution d ON c.remote_ip = d.remote_ip
        WHERE
                               c.remote_ip != '127.0.0.1'
        ORDER BY
            c.connection_count DESC
        LIMIT 1000
        """, conn)
        conn.close()
    except:
        logging.error("Database not ready (yet)")
    logging.debug("Close database")
    return df

def start_db_updater(interval_seconds=60, db_path='connexions.db'):
    def updater():
        while True:
            update_connections_db(db_path)
            time.sleep(interval_seconds)
    threading.Thread(target=updater, daemon=True).start()
    logging.info(f"Update thread run (intervalle : {interval_seconds}s).")

# --- Application Dash ---
app = Dash(__name__)
app.title = "HoCoYs - Host connected to your system"

app.layout = html.Div([
    html.H1("Host connected to your system"),
    html.Div([
        html.Label('Select a grouping criteria:'),
        dcc.Dropdown(
            id='agg-field',
            options=[
                {'label': 'Process name (pname)', 'value': 'pname'},
                {'label': 'Remote IP', 'value': 'remote_ip'},
                {'label': 'Hostname (gethostbyaddr)', 'value': 'hostname'},
                {'label': 'Description (whois)', 'value': 'desc'},
                {'label': 'Country (whois)', 'value': 'contry'},
            ],
            value='contry',
            clearable=False,
            style={'width': '300px'}
        )
    ], style={'marginBottom': '0px'}),
    dcc.Graph(
        id='pname-histogram',
        figure={}
    ),
    dcc.Store(id='pname-filter-store'),
    html.Div([html.Button('Clear filter', id='clear-filter', n_clicks=0), html.Span(id='filter-indicator', style={'marginLeft': '10px'})]),
    dash_table.DataTable(
        id='connexions-table',
        sort_action='native',
        filter_action='native',
        columns=[{"name": col, "id": col} for col in get_connections_data().columns],
        data=get_connections_data().to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={
            'height': 'auto',
            'minWidth': '100px', 'width': '100px', 'maxWidth': '180px',
            'whiteSpace': 'normal'
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  #screen efresh 1minute
        n_intervals=0
    )
])

@app.callback(
    Output('connexions-table', 'data'),
    Output('filter-indicator', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('agg-field', 'value'),
    Input('pname-filter-store', 'data')
)
def update_table(n, agg_field, filter_data):
    df = get_connections_data()
    indicator = ''
    field = None
    value = None
    # Validate filter_data matches current agg_field. If not, ignore stored filter.
    if filter_data and 'field' in filter_data and filter_data.get('value'):
        field = filter_data['field']
        value = filter_data['value']
        if field != agg_field:
            # stored filter is for a different aggregation field; ignore it
            field = None
            value = None
        # handle 'Other' by excluding top N values for the selected field
    if filter_data and field and value:
        if value == 'Other':
            # recompute top N to know which to exclude
            agg = compute_agg(df, field)
            agg = agg.sort_values('connection_count', ascending=False)
            top_vals = agg.head(TOP_N)[field].tolist()
            df = df[~df[field].isin(top_vals)]
            indicator = f"Filtered: Other (excluding top {TOP_N} by {field})"
        else:
            df = df[df[field] == value]
            indicator = f"Filtered: {field} = {value}"
    return df.to_dict('records'), indicator


@app.callback(
    Output('pname-filter-store', 'data'),
    Input('pname-histogram', 'clickData'),
    Input('clear-filter', 'n_clicks'),
    State('agg-field', 'value'),
    prevent_initial_call=True
)
def handle_hist_click(clickData, clear_clicks, agg_field):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'clear-filter':
        return {'field': None, 'value': None}
    if triggered_id == 'pname-histogram' and clickData:
        # clickData structure: points -> [ { 'x': 'value', ... } ]
        try:
            val = clickData['points'][0]['x']
        except Exception:
            val = None
        return {'field': agg_field, 'value': val}
    return {'field': None, 'value': None}


@app.callback(
    Output('pname-histogram', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input('agg-field', 'value')
)
def update_pname_hist(n, agg_field):
    # Build aggregated data by pname
    df = get_connections_data()
    if df is None or df.empty:
        # empty figure
        return {
            'data': [],
            'layout': {'title': 'No data available'}
        }
    # If connection_count exists use it, otherwise count occurrences
    field = agg_field if agg_field in df.columns else 'pname'
    # Using default metric 'count' here (table callback may use selected metric via Input)
    # The histogram should reflect the metric selected in the UI — read it from Request (we'll add Input)
    agg = compute_agg(df, field, 'sum_connection_count')
    agg = agg.sort_values('connection_count', ascending=False)
    # Limit to top N processes and group the rest as 'Other'
    if len(agg) > TOP_N:
        top = agg.head(TOP_N).copy()
        others = agg.iloc[TOP_N:]
        other_sum = others['connection_count'].sum()
        other_row = pd.DataFrame([{agg_field: 'Other', 'connection_count': other_sum}])
        display_df = pd.concat([top, other_row], ignore_index=True)
    else:
        display_df = agg

    # build bar chart data
    return {
        'data': [
            {
                'type': 'bar',
                'x': display_df[agg_field].tolist(),
                'y': display_df['connection_count'].tolist(),
                'marker': {'color': 'steelblue'}
            }
        ],
        'layout': {
            'title': f'Connections aggregated by {agg_field} (top {TOP_N})',
            'xaxis': {'title': f'{agg_field}', 'tickangle': -45},
            'yaxis': {'title': 'Connection count'},
            'margin': {'b': 150}
        }
    }

# --- Point d'entrée ---
if __name__ == '__main__':
    logging.info("Starting backend")
    init_db()
    start_db_updater(interval_seconds=10)  # Mise à jour toutes les 1 minute
    logging.info("Starting Dash app")
    app.run(debug=False, port=8050)

