#!/usr/bin/env python3

import logging
import time
import os
import yaml
import sys
import requests
import json
import base64
import hashlib
import hmac
from prometheus_client import write_to_textfile, start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily, CounterMetricFamily

log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=os.environ.get("LOGLEVEL", "INFO"))

settings = {}


def _settings():
    global settings

    settings = {
        'kraken_exporter': {
            'prom_folder': '/var/lib/node_exporter',
            'interval': 60,
            'export': 'text',
            'listen_port': 9310,
            'url': 'https://api.kraken.com',
            'trade_symbols': [],
            'timeout': 5,
        },
    }
    config_file = '/etc/kraken_exporter/kraken_exporter.yaml'
    cfg = {}
    if os.path.isfile(config_file):
        with open(config_file, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
    if cfg.get('kraken_exporter'):
        if cfg['kraken_exporter'].get('prom_folder'):
            settings['kraken_exporter']['prom_folder'] = cfg['kraken_exporter']['prom_folder']
        if cfg['kraken_exporter'].get('interval'):
            settings['kraken_exporter']['interval'] = cfg['kraken_exporter']['interval']
        if cfg['kraken_exporter'].get('url'):
            settings['kraken_exporter']['url'] = cfg['kraken_exporter']['url']
        if cfg['kraken_exporter'].get('export') in ['text', 'http']:
            settings['kraken_exporter']['export'] = cfg['kraken_exporter']['export']
        if cfg['kraken_exporter'].get('listen_port'):
            settings['kraken_exporter']['listen_port'] = cfg['kraken_exporter']['listen_port']
        if cfg['kraken_exporter'].get('timeout'):
            settings['kraken_exporter']['timeout'] = int(cfg['kraken_exporter']['timeout'])


class KrakenCollector:
    rates = []
    symbols = {}

    def __init__(self):
        self._getExchangeRates()

    def _translate(currency):
        r = currency
        if currency == 'DASH':
            r = 'DSH'
        if currency == 'XBT':
            r = 'BTC'
        if currency == 'DOGE':
            r = 'XDG'
        return r

    def _getSymbols(self):
        """
        Gets the list of symbols, if none are configured in the settings file. Only one call, at start.

        Unfortunately, this only works over the v1 API
        """
        path = "/0/public/AssetPairs"
        r = requests.get(
            settings['kraken_exporter']['url'] + path,
            verify=True,
            timeout=settings['kraken_exporter']['timeout']
        )
        if r and r.status_code == 200 and r.json().get('result'):
            symbols = r.json()['result']
            for symbol in symbols:
                if symbols[symbol]['altname'].endswith(('.d')):
                    continue
                settings['kraken_exporter']['trade_symbols'].append(symbols[symbol]['altname'].upper())
        else:
            log.warning('Could not retrieve symbols. Response follows.')
            log.warning(r.headers)
            log.warning(r.json())

        log.debug('Found the following symbols: {}'.format(settings['kraken_exporter']['trade_symbols']))

    def _getExchangeRates(self):
        result = []
        if not settings['kraken_exporter']['trade_symbols']:
            self._getSymbols()
        if settings['kraken_exporter']['trade_symbols']:
            pairs_string = ','.join(settings['kraken_exporter']['trade_symbols'])
            path = "/0/public/Ticker"

            log.debug('Pairs: {}'.format(pairs_string))
            r = None
            try:
                r = requests.get(
                    settings['kraken_exporter']['url'] + path,
                    params={'pair': pairs_string},
                    verify=True,
                    timeout=settings['kraken_exporter']['timeout']
                )
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.packages.urllib3.exceptions.ReadTimeoutError
            ) as e:
                log.warning(e)

            if r:
                if r.status_code == 200 and r.json().get('result'):
                    tickers = r.json()['result']
                    for ticker in tickers:
                        log.debug('Got {} - {}'.format(ticker, tickers[ticker]))
                        pair = {
                            'source_currency': KrakenCollector._translate(ticker[0:3]),
                            'target_currency': KrakenCollector._translate(ticker[-3:]),
                            'value': float(tickers[ticker]['c'][0]),
                        }

                        if ticker.startswith('X') and len(ticker) == 8:
                            pair['source_currency'] = KrakenCollector._translate(ticker[1:4])

                        result.append(pair)
                else:
                    log.warning('Could not retrieve ticker data. Response follows.')
                    log.warning(r.headers)
                    log.warning(r.json())
        log.debug('Found the following ticker rates: {}'.format(result))
        if result:
            self.rates = result

    def collect(self):
        metrics = {
            'exchange_rate': GaugeMetricFamily(
                'exchange_rate',
                'Current exchange rates',
                labels=['source_currency', 'target_currency', 'exchange']
            ),
        }
        for rate in self.rates:
            metrics['exchange_rate'].add_metric(
                value=rate['value'],
                labels=[
                    rate['source_currency'],
                    rate['target_currency'],
                    'kraken'
                ]
            )

        for m in metrics.values():
            yield m


def _collect_to_text():
    global exchange_rates
    while True:
        e = KrakenCollector()
        write_to_textfile('{0}/kraken_exporter.prom'.format(settings['kraken_exporter']['prom_folder']), e)
        time.sleep(int(settings['kraken_exporter']['interval']))


def _collect_to_http():
    REGISTRY.register(KrakenCollector())
    start_http_server(int(settings['kraken_exporter']['listen_port']))
    while True:
        time.sleep(int(settings['kraken_exporter']['interval']))


if __name__ == '__main__':
    _settings()
    log.debug('Loaded settings: {}'.format(settings))
    if settings['kraken_exporter']['export'] == 'text':
        _collect_to_text()
    if settings['kraken_exporter']['export'] == 'http':
        _collect_to_http()
