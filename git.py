import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
import base64
import json

# Initialize Dash app
app = dash.Dash(__name__)

# Dogecoin API details (using Blockcypher or another service)
DOGE_API_URL = "https://api.blockcypher.com/v1/doge/main/addrs/{}/full"

# GitHub API details
GITHUB_TOKEN = "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"  # Replace with your GitHub token
GITHUB_REPO = "hashmagic420/TRACKWALLETS-DOGE"  # The repo to post to (user/repo format)
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"  # Base API URL

# Function to create or update a file on GitHub
def commit_to_github(file_path, content, commit_message):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get the current content to see if the file exists
    file_url = GITHUB_API_URL + file_path
    response = requests.get(file_url, headers=headers)

    if response.status_code == 200:
        # File exists, we need to update it
        sha = response.json()["sha"]
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            "sha": sha  # The SHA of the existing file
        }
    else:
        # File doesn't exist, create a new one
        data = {
            "message": commit_message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
        }

    response = requests.put(file_url, headers=headers, data=json.dumps(data))

    if response.status_code == 201 or response.status_code == 200:
        print(f"Successfully committed to GitHub: {file_path}")
    else:
        print(f"Failed to commit to GitHub: {response.status_code}, {response.text}")

# Function to track wallet transactions
def track_wallet_transactions(wallet_address):
    try:
        url = DOGE_API_URL.format(wallet_address)
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            transactions = data.get('txs', [])
            
            if transactions:
                transaction_info = f"Wallet: {wallet_address}\n"
                for tx in transactions:
                    tx_hash = tx.get('hash')
                    tx_value = sum(output.get('value', 0) for output in tx.get('outputs', [])) / 1e8  # Convert from satoshis
                    transaction_info += f"  Transaction Hash: {tx_hash}\n  Value: {tx_value} DOGE\n\n"
                
                # Commit the transaction info to GitHub
                file_name = f"wallet_{wallet_address}.txt"
                commit_message = f"Transaction update for wallet {wallet_address}"
                commit_to_github(file_name, transaction_info, commit_message)
                
                return transaction_info
            else:
                return f"Wallet: {wallet_address} - No recent transactions found.\n"
        else:
            return f"Error: Unable to fetch data for wallet {wallet_address}. Status Code: {response.status_code}\n"
    except Exception as e:
        return f"An error occurred while tracking wallet {wallet_address}: {e}\n"

# Dash layout
app.layout = html.Div([
    html.H1("Dogecoin Wallet Tracker"),
    
    dcc.Textarea(id='wallet-input', placeholder='Enter Dogecoin wallet addresses (one per line)', style={'width': '100%', 'height': 200}),
    html.Button('Track Wallets', id='track-button', n_clicks=0),
    
    html.Hr(),
    html.Div(id='transaction-log', style={'whiteSpace': 'pre-line'}),
])

# Dash callback to update the log and track the wallet
@app.callback(
    Output('transaction-log', 'children'),
    [Input('track-button', 'n_clicks')],
    [State('wallet-input', 'value')]
)
def update_output(n_clicks, wallet_addresses):
    if n_clicks > 0 and wallet_addresses:
        wallet_list = wallet_addresses.splitlines()
        log = ""
        for wallet in wallet_list:
            if wallet.strip():  # Ignore empty lines
                log += track_wallet_transactions(wallet.strip())
        return log
    return "Enter wallet addresses and click 'Track Wallets'."

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
