# ticker-exporters

Allows exporting ticker and account data, for gathering with [Prometheus](https://prometheus.io).

Merge/Pull requests are welcomed, I reserve however the right to accept/deny them.

This project is hosted on [gitlab.com/tlex/ticker-exporters](https://gitlab.com/tlex/ticker-exporters) and mirrored on [github.com/tlex/ticker-exporters](https://github.com/tlex/ticker-exporters).

## Supported:
> Note! Some exporters require API credentials.

Make sure that the API keys you configure are **read only** keys!

### Account Balance Only:
*   [etherscan / ETH](https://etherscan.io) - API credentials required
*   [Ripple / XRP](https://xrpcharts.ripple.com/)
*   [Stellar / XLM](https://www.stellar.org/account-viewer/)

### Ticker Data Only:
*   [GDAX](https://www.gdax.com)
*   [Abucoins](https://abucoins.com/)
*   [BitStamp](https://www.bitstamp.net)

### Both Account Balance and Ticker Data
*   [BitFinex](https://www.bitfinex.com) - API credentials required for account balance
*   [Quoine](https://www.quoine.com) (with the two brands [Quoinex](https://trade.quoinex.com) and [Qryptos](https://trade.qryptos.com)) - API credentials required for account balance
*   [Poloniex](https://poloniex.com) - API credentials required for account balance - **WARNING!** The library used is [poloniex](https://github.com/s4w3d0ff/python-poloniex). This library isn't available over PyPi.
*   [Binance](https://www.binance.com) - API credentials are required for both account balance and ticker data
*   [Kraken](https://www.kraken.com) - API credentials are required for account balance

## Requirements
*   python3 (I use 3.5.2 on Ubuntu 16.04)
*   pip3 (I use 8.1.1, since it was installed with `apt`)
*   every exporter has a `*_requirements.txt` file. Install the modules with `pip3 install -r file__requirements.txt`. Alternatively, you can install all the requirements: `pip3 install -r all_requirements.txt`.

## Configuration
All the exporters try to load the configuration file located in `/etc/*_exporter/*.exporter.yaml`. For example, the
`bitfinex_exporter` will look for `/etc/bitfinex_exporter/bitfinex_exporter.yaml`

### Configuration File Structure
```yaml
type_exporter:
  option1: value
  option2: value
  option3:
    - list item 1
    - list item 2
```

### Common Options
The following options are supported by all exporters:
```yaml
  prom_folder: /var/lib/node_exporter
  interval: 60
  export: text
  listen_port: 9302
```

*   `prom_folder` (string) - for write_to_textfile - the folder on the HDD where the node_exporter looks for the .prom files
*   `interval` (integer / string) - the data gathering interval in seconds
*   `export` (string) - switch for `text`/`html` - use `node_exporter` to collect the metrics or open a port for http connection from prometheus
*   `listen_port` (integer / string) - the TCP port to open, if `export` has been set to `text`

Most exporters also support an `url` (string) option. Exceptions are:
*   `quoine_exporter` - there are two urls used, one for Quoinex and one for Qryptos. These URLs are hard coded.
*   `binance_exporter` - the library (python-binance) provides the URL
*   `poloniex_exporter` - the library (poloniex) provides the URL

### Additional Options Specific for Each Exporter
#### `abucoins_exporter`
This is listed separately, since the API credentials are not yet used.
*   `api_key` (string) - the API key from the exchange
*   `api_secret` (string) - the API secret from the exchange

#### `bitfinex_exporter` + `poloniex_exporter` + `quoine_exporter` + `binance_exporter`
*   `api_key` (string) - the API key from the exchange
*   `api_secret` (string) - the API secret from the exchange

#### `kraken_exporter`
*   `api_key` (string) - the API key from the exchange
*   `private_key` (string) - the API private key from the exchange

#### `etherscan_exporter`
*   `api_key` (string) - the etherscan API key
*   `addresses` (list of strings) - the list of ETH addresses for which to collect the balance
*   `tokens` (list of dictionaries) - the list of *contract addresses*. The exporter will check for every address listed above if any of the contract addresses listed here has a token balance

Example for the OmiseGO token:
```yaml
etherscan_exporter:
  addresses:
    - 0x90833394db1b53f08b9d97dab8beff69fcf3ba49
  tokens:
    - contract: '0xd26114cd6EE289AccF82350c8d8487fedB8A0C07'
      name: 'OmiseGO'
      short: 'OMG'
      decimals: 18
    - contract: '0xab95e915c123fded5bdfb6325e35ef5515f1ea69'
      name: 'XENON'
      short: 'XNN'
      decimals: 18
```

#### `kraken_exporter`
*   `timeout` (integer / string) - timeout in seconds for the requests to the API

#### `ripple_exporter` + `stellar_exporter`
*   `addresses` (list of strings) - the list of ETH/XLM addresses for which to collect the balance

## `systemd` Unit File Example
```
[Unit]
Description=Prometheus Bitfinex Exporter

[Service]
ExecStart=/usr/local/sbin/bitfinex_exporter.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## Full Configuration Examples
```yaml
abucoins_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  export: 'text'
  listen_port: 9312
  url: 'https://api.abucoins.com'
binance_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '10'
  export: 'text'
  listen_port: 9315
  api_key: 'my_api_key'
  api_secret: 'my_api_secret'
bitfinex_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  api_key: 'my_api_key'
  api_secret: 'my_api_secret'
  export: 'text'
  listen_port: 9309
  url: 'https://api.bitfinex.com'
bitstamp_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '5'
  export: 'text'
  listen_port: 9313
  url: 'https://www.bitstamp.net/api'
etherscan_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  api_key: 'my_api_key'
  export: 'text'
  listen_port: 9308
  url: 'https://api.etherscan.io/api'
  addresses: ['0x90833394db1b53f08b9d97dab8beff69fcf3ba49']
  tokens: [{'short': 'OMG', 'decimals': 18, 'name': 'OmiseGO', 'contract': '0xd26114cd6EE289AccF82350c8d8487fedB8A0C07'}, {'short': 'INSP', 'decimals': 0, 'name': 'INS Promo', 'contract': '0x52903256dd18d85c2dc4a6c999907c9793ea61e3'}, {'short': 'VIU', 'decimals': 18, 'name': 'VIU', 'contract': '0x519475b31653e46d20cd09f9fdcf3b12bdacb4f5'}, {'short': 'DATA', 'decimals': 18, 'name': 'DATAcoin', 'contract': '0x0cf0ee63788a0849fe5297f3407f701e122cc023'}, {'short': 'XNN', 'decimals': 18, 'name': 'XENON', 'contract': '0xab95e915c123fded5bdfb6325e35ef5515f1ea69'}]
gdax_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '5'
  export: 'text'
  listen_port: 9306
kraken_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  export: 'text'
  listen_port: 9310
  url: 'https://api.kraken.com'
  timeout: '30'
  api_key: 'my_api_key'
  private_key: 'my_private_key'
poloniex_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  export: 'text'
  listen_port: 9311
  timeout: '30'
  api_key: 'my_api_key'
  api_secret: 'my_api_secret'
quoine_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '10'
  export: 'text'
  listen_port: 9314
  api_key: 'my_api_key'
  api_secret: 'my_api_secret'
ripple_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  url: 'https://data.ripple.com'
  addresses: ['rLW9gnQo7BQhU6igk5keqYnH3TVrCxGRzm']
stellar_exporter:
  prom_folder: '/var/lib/node_exporter'
  interval: '60'
  export: 'text'
  listen_port: 9308
  accounts: ['GCO2IP3MJNUOKS4PUDI4C7LGGMQDJGXG3COYX3WSB4HHNAHKYV5YL3VC']
```

## Donations
*   ETH: 0x90833394dB1b53f08B9D97dab8BEFf69FCf3bA49
