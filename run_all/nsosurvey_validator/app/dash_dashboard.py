import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Dash app (can be mounted under the FastAPI app)
dash_app = dash.Dash(
    __name__,
    title="Survey Data Validation Dashboard",
    url_base_pathname="/dashboard/",
    external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
)

dash_app.layout = html.Div([
    html.H1("Survey Data Validation Dashboard", style={"textAlign": "center", "color": "#2c3e50"}),
    
    html.Div([
        html.Label("Select Validation Type:"),
        dcc.RadioItems(
            id="validation-type",
            options=[
                {"label": "Record-Level Anomalies", "value": "record"},
                {"label": "Aggregate Anomalies", "value": "aggregate"},
                {"label": "Cluster Anomalies", "value": "cluster"},
                {"label": "Integrity Checks", "value": "checks"},
            ],
            value="record",
            inline=True,
        ),
    ], style={"padding": "20px", "backgroundColor": "#f8f9fa", "marginBottom": "20px"}),
    
    html.Div([
        html.Label("Upload Data File:"),
        dcc.Upload(
            id="upload-data",
            children=html.Div([
                "Drag & Drop or ",
                html.A("Select CSV/XLSX File")
            ]),
            style={
                "width": "100%", "height": "60px", "lineHeight": "60px",
                "borderWidth": "1px", "borderStyle": "dashed", "borderRadius": "5px",
                "textAlign": "center", "marginBottom": "10px"
            },
            multiple=False,
        ),
    ], style={"padding": "10px"}),
    
    html.Div([
        html.Label("Group By Column (Aggregate/Cluster):"),
        dcc.Dropdown(id="groupby-column", options=[], value=None),
    ], style={"padding": "10px", "marginBottom": "10px"}),
    
    html.Div([
        html.Label("Value Column:"),
        dcc.Dropdown(id="value-column", options=[], value=None),
    ], style={"padding": "10px", "marginBottom": "10px"}),
    
    html.Div([
        html.Button("Run Validation", id="run-validation", n_clicks=0,
                     style={"backgroundColor": "#3498db", "color": "white", "border": "none",
                            "padding": "10px 20px", "borderRadius": "5px", "cursor": "pointer"}),
    ], style={"padding": "10px"}),
    
    html.Div(id="validation-results", style={"marginTop": "20px", "minHeight": "400px"}),
    
    html.Div(id="error-message", style={"marginTop": "10px", "color": "red", "fontSize": "12px"}),
])


@dash_app.callback(
    [Output("groupby-column", "options"),
     Output("value-column", "options")],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def update_columns(contents, filename):
    if contents is None:
        return [], []
    
    # Decode and load data
    import base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    import tempfile
    import os
    
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}")
    tmp_file.write(decoded)
    tmp_file.close()
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(tmp_file.name)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(tmp_file.name)
        else:
            df = pd.read_csv(tmp_file.name)
        
        numeric_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64']]
        all_cols = list(df.columns)
        
        gb_options = [{"label": c, "value": c} for c in numeric_cols if c != "weight"]
        val_options = [{"label": c, "value": c} for c in numeric_cols]
        
        return gb_options, val_options
    finally:
        os.unlink(tmp_file.name)


@dash_app.callback(
    Output("validation-results", "children"),
    Output("error-message", "children"),
    [Input("run-validation", "n_clicks")],
    [State("upload-data", "contents"),
     State("validation-type", "value"),
     State("groupby-column", "value"),
     State("value-column", "value")],
)
def run_validation(n_clicks, contents, val_type, groupby_col, value_col):
    if n_clicks == 0 or contents is None:
        return html.Div(), ""
    
    import base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    import tempfile, os
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp_file.write(decoded)
    tmp_file.close()
    
    try:
        df = pd.read_csv(tmp_file.name)
        
        # Clean up
        os.unlink(tmp_file.name)
        
        if val_type == "record":
            # Record-level anomaly detection
            numeric_cols = [c for c in df.columns if df[c].dtype in ['float64', 'int64']]
            feature_cols = numeric_cols[:8]
            
            if len(feature_cols) == 0:
                return html.Div("No numeric columns found for anomaly detection"), ""
            
            # Simple z-score based anomaly detection
            from scipy import stats
            anomaly_scores = {}
            anomaly_flags = {}
            
            for col in feature_cols:
                try:
                    z_scores = np.abs(stats.zscore(df[col].dropna().values))
                    threshold = 2.5
                    anomalies = z_scores > threshold
                    anomaly_scores[col] = {
                        "mean_z_score": float(np.mean(z_scores)),
                        "max_z_score": float(np.max(z_scores)),
                        "anomaly_count": int(anomalies.sum()),
                        "anomaly_percentage": float(anomalies.mean() * 100),
                    }
                except:
                    anomaly_scores[col] = {"error": "Could not compute"}
            
            # Create a table of results
            fig = go.Figure()
            for col in anomaly_scores:
                if "error" not in anomaly_scores[col]:
                    z_scores = np.abs(stats.zscore(df[col].dropna().values))
                    fig.add_trace(go.Box(y=z_scores, name=col, showlegend=False))
            
            fig.update_layout(title="Z-Score Distribution by Column", height=500)
            
            return html.Div([
                html.H3("Record-Level Anomaly Detection"),
                html.P(f"Total records: {len(df)}"),
                html.Div([
                    html.Div([
                        html.H4(col),
                        html.P(f"Mean Z: {anomaly_scores[col].get('mean_z_score', 0):.2f}"),
                        html.P(f"Max Z: {anomaly_scores[col].get('max_z_score', 0):.2f}"),
                        html.P(f"Anomalies: {anomaly_scores[col].get('anomaly_count', 0)} ({anomaly_scores[col].get('anomaly_percentage', 0):.1f}%)"),
                    ], style={"padding": "10px", "backgroundColor": "#fff", "marginBottom": "5px", "borderRadius": "3px"})
                    for col in anomaly_scores if "error" not in anomaly_scores[col]
                ]),
                dcc.Graph(figure=fig),
            ])
            
        elif val_type == "aggregate" and groupby_col and value_col:
            # Aggregate anomaly detection
            try:
                grouped = df.groupby(groupby_col)[value_col].agg(['mean', 'count', 'std']).reset_index()
                
                # Simple trend analysis
                if len(grouped) > 3:
                    x = np.arange(len(grouped))
                    slope, intercept = np.polyfit(x, grouped['mean'].values, 1)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=grouped[groupby_col].astype(str),
                        y=grouped['mean'].values,
                        mode='markers+lines',
                        name=f'Mean {value_col}'
                    ))
                    fig.add_trace(go.Scatter(
                        x=grouped[groupby_col].astype(str),
                        y=slope * x + intercept,
                        mode='lines',
                        name=f'Trend (slope={slope:.4f})',
                        line={'dash': 'dash', 'color': 'red'}
                    ))
                    
                    # Flag outliers (values more than 2 std dev from mean)
                    mean_val = grouped['mean'].mean()
                    std_val = grouped['mean'].std()
                    fig.add_hline(y=mean_val + 2*std_val, line_dash='dot', line_color='orange',
                                  annotation_text=f"Mean + 2σ = {mean_val + 2*std_val:.2f}")
                    fig.add_hline(y=mean_val - 2*std_val, line_dash='dot', line_color='orange')
                    
                    return html.Div([
                        html.H3("Aggregate-Level Anomaly Detection"),
                        html.P(f"Grouping column: {groupby_col}"),
                        html.P(f"Value column: {value_col}"),
                        html.P(f"Groups analyzed: {len(grouped)}"),
                        html.P(f"Trend slope: {slope:.4f} ({'increasing' if slope > 0 else 'decreasing'})"),
                        dcc.Graph(figure=fig),
                    ])
            except Exception as e:
                return html.Div(), f"Error in aggregate analysis: {str(e)}"
            
        elif val_type == "cluster" and groupby_col and value_col:
            # Cluster-level analysis
            try:
                clustered = df.groupby(groupby_col)[value_col].value_counts().reset_index()
                
                fig = go.Figure(data=go.Bar(
                    x=clustered[groupby_col].astype(str).head(20),
                    y=clustered[value_col].head(20),
                    marker_color='steelblue'
                ))
                
                fig.update_layout(title=f"Distribution of {value_col} by {groupby_col}",
                                  xaxis_title=groupby_col, yaxis_title=value_col, height=500)
                
                return html.Div([
                    html.H3("Cluster-Level Analysis"),
                    html.P(f"Grouping column: {groupby_col}"),
                    html.P(f"Value column: {value_col}"),
                    dcc.Graph(figure=fig),
                ])
            except Exception as e:
                return html.Div(), f"Error in cluster analysis: {str(e)}"
        
        return html.Div("Select validation type and configure parameters"), ""
        
    except Exception as e:
        return html.Div(), f"Error processing data: {str(e)}"


# Mount the Dash app under FastAPI
def mount_dash_app(fastapi_app: FastAPI, path: str = "/dashboard/"):
    """Mount Dash app under FastAPI"""
    fastapi_app.mount(path, dash_app.server)


mount_dash_app(app)

if __name__ == "__main__":
    import uvicorn
    # Run both FastAPI and Dash
    uvicorn.run(app, host="0.0.0.0", port=8000)