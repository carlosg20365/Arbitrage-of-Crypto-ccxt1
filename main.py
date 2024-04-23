import ccxt
import itertools
from logger_config import setup_logger
import asyncio
from arbitrage.data_to_csv import create_csv
import logging
from logging.handlers import RotatingFileHandler
from api_config import exchange_credentials

# Configura o logger usando a função do módulo logger_config.py
logger = setup_logger('D:\\test\\', 'arbitrage_log.log')

def setup_logger(log_directory, log_file):
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    )
    log_handler = RotatingFileHandler(
        log_directory + log_file,
        mode='a',
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding=None,
        delay=0
    )
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)

    logger = logging.getLogger('arbitrage_logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

    return logger


# Defina um limiar de discrepância para notificações ou ações
DISCREPANCY_THRESHOLD = 0.50  # 1% de discrepância

async def compare_prices():
    exchanges = {}
    for exchange_name, credentials in exchange_credentials.items():
        exchange = getattr(ccxt, exchange_name)({
            'apiKey': credentials['api_key'],
            'secret': credentials['api_secret'],
            **credentials.get('passphrase', {})
        })
        exchanges[exchange_name] = exchange

    markets = {exchange_name: exchange.fetch_markets() for exchange_name, exchange in exchanges.items()}

    symbols_sets = {exchange_name: {market['symbol'] for market in market_list if market['symbol'].endswith(('USDT', 'USDC'))} for exchange_name, market_list in markets.items()}
    common_symbols = set.intersection(*symbols_sets.values())
    symbols = list(common_symbols)

    # Inicialize comparison_data fora do loop
    csv_filename = 'discrepancies.csv'

    while True:
        try:
            comparison_data = []

            for symbol in symbols:
                try:
                    ticker_data = {exchange_name: exchange.fetch_ticker(symbol) for exchange_name, exchange in exchanges.items()}

                    if all(ticker['last'] is not None for ticker in ticker_data.values()):
                        prices = {exchange_name: ticker['last'] for exchange_name, ticker in ticker_data.items()}

                        for (exchange_a, price_a), (exchange_b, price_b) in itertools.combinations(prices.items(), 2):
                            percentage_discrepancy = ((price_a - price_b) / price_b) * 100
                            if abs(percentage_discrepancy) > DISCREPANCY_THRESHOLD:
                                logger.info(f'Discrepância significativa encontrada para {symbol}: {exchange_a}-{exchange_b}: {percentage_discrepancy:.2f}%')

                        comparison_data.append({
                            'Symbol': symbol,
                            **{f'{exchange_name} Price': price for exchange_name, price in prices.items()},
                            **{f'Percentage Discrepancy {exchange_a}-{exchange_b}': ((prices[exchange_a] - prices[exchange_b]) / prices[exchange_b]) * 100
                               for (exchange_a, price_a), (exchange_b, price_b) in itertools.combinations(prices.items(), 2)}
                        })

                    else:
                        logger.warning(f'Invalid prices for {symbol}. Skipping...')

                except ccxt.NetworkError as e:
                    logger.error(f'Network Error fetching {symbol}: {str(e)}')
                except ccxt.ExchangeError as e:
                    logger.error(f'Exchange Error fetching {symbol}: {str(e)}')
                except ccxt.BaseError as e:
                    logger.error(f'CCXT Base Error fetching {symbol}: {str(e)}')
                except Exception as e:
                    logger.error(f'Error fetching {symbol}: {str(e)}')

            create_csv(comparison_data, csv_filename)

        except Exception as e:
            logger.critical(f'Error in compare_prices: {str(e)}')
            # TODO: Add exception handling for create_csv in case it fails

# Executa a função de comparação de preços
if __name__ == '__main__':
    asyncio.run(compare_prices())
