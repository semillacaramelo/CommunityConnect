"""
Module for fetching market data from Deriv API
Based on official Deriv API documentation
"""
import pandas as pd
import numpy as np
import asyncio
import time
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger(__name__)

class DataFetcher:
    def __init__(self, connector):
        self.connector = connector
        self.last_fetch_time = {}  # Para limitar la frecuencia de solicitudes por símbolo
        self.fetch_cooldown = 10  # Tiempo mínimo entre solicitudes para el mismo símbolo
        self.cache = {}  # Caché simple de datos por símbolo y intervalo

    async def fetch_historical_data(self, symbol, interval, count=1000, retry_attempts=3, use_cache=True):
        """
        Fetch historical candlestick data

        Args:
            symbol: Trading symbol (e.g., "frxEURUSD")
            interval: Candle interval in seconds
            count: Number of candles to fetch
            retry_attempts: Number of retry attempts
            use_cache: Whether to use cached data when possible
        """
        cache_key = f"{symbol}_{interval}"

        # Verificar limitación de frecuencia
        current_time = time.time()
        if symbol in self.last_fetch_time:
            time_since_last = current_time - self.last_fetch_time[symbol]
            if time_since_last < self.fetch_cooldown:
                # Si tenemos caché y estamos dentro del periodo de cooldown, usar caché
                if use_cache and cache_key in self.cache:
                    logger.debug(f"Using cached data for {symbol} (cooldown: {self.fetch_cooldown - time_since_last:.1f}s)")
                    return self.cache[cache_key]

                # Si necesitamos esperar, calculamos el tiempo restante
                wait_time = self.fetch_cooldown - time_since_last
                logger.debug(f"Rate limiting for {symbol}, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        # Intentar hasta el número de reintentos especificado
        for attempt in range(retry_attempts):
            try:
                # Validate symbol format
                if not symbol.startswith(('frx', 'R_')):
                    logger.error(f"Invalid symbol format: {symbol}")
                    return None

                # Verificar estado de conexión
                if not await self.connector.check_connection():
                    logger.warning(f"Connection not available for {symbol} data fetch, attempt {attempt+1}/{retry_attempts}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))  # Espera creciente entre intentos
                    continue

                # Request historical data
                # Pedimos más candles para compensar posibles datos faltantes
                adjusted_count = min(int(count * 1.2), 5000)  # 20% más, máximo 5000

                request = {
                    "ticks_history": symbol,
                    "adjust_start_time": 1,
                    "count": adjusted_count,
                    "end": "latest",
                    "granularity": interval,
                    "style": "candles",
                    "req_id": self.connector._get_request_id()
                }

                response = await self.connector.send_request(request)

                # Actualizar timestamp de última solicitud
                self.last_fetch_time[symbol] = time.time()

                if "error" in response:
                    error_msg = response["error"]["message"]
                    logger.error(f"Error fetching historical data: {error_msg}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                # Validate response structure
                if "candles" not in response:
                    logger.error("Invalid response: missing candles data")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                candles = response["candles"]

                # Verificar si tenemos suficientes velas
                if len(candles) < count:
                    logger.warning(f"Received fewer candles than requested: {len(candles)} vs {count}")
                    # Si es demasiado poco, podríamos reintentar
                    if len(candles) < count * 0.5 and attempt < retry_attempts - 1:  # Menos del 50% de lo solicitado
                        logger.warning(f"Insufficient data ({len(candles)} candles), retrying... {attempt+1}/{retry_attempts}")
                        await asyncio.sleep(2)
                        continue

                # Create DataFrame
                df = pd.DataFrame([{
                    'time': candle['epoch'],
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close'])
                } for candle in candles])

                # Convert timestamp and set index
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)

                # Sort index to ensure chronological order
                df.sort_index(inplace=True)

                # Guardar en caché
                self.cache[cache_key] = df

                logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
                return df

            except Exception as e:
                logger.error(f"Error in fetch_historical_data: {str(e)}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 * (attempt + 1))

        # Si llegamos aquí, todos los intentos fallaron
        # Intentar devolver caché como último recurso
        if use_cache and cache_key in self.cache:
            logger.warning(f"All fetch attempts failed for {symbol}, using cached data")
            return self.cache[cache_key]

        return None

    async def fetch_sufficient_data(self, symbol, interval, min_required_samples, max_attempts=3):
        """
        Asegura que suficientes muestras sean obtenidas para el análisis

        Args:
            symbol: Trading symbol
            interval: Candle interval in seconds
            min_required_samples: Mínima cantidad de muestras requeridas
            max_attempts: Número máximo de intentos
        """
        for attempt in range(max_attempts):
            # Calcular cuántas velas necesitamos con un margen
            count_with_margin = min_required_samples * 1.5
            # Limitado a 3000 para no exceder límites de API
            count_to_fetch = min(3000, int(count_with_margin))

            logger.info(f"Fetching {count_to_fetch} candles to ensure {min_required_samples} samples (attempt {attempt+1})")
            df = await self.fetch_historical_data(symbol, interval, count=count_to_fetch)

            if df is None:
                logger.warning(f"Failed to fetch data, attempt {attempt+1}/{max_attempts}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(3)
                continue

            # Verificar si tenemos suficientes datos
            if len(df) >= min_required_samples:
                logger.info(f"Successfully obtained {len(df)} samples (needed {min_required_samples})")
                return df
            else:
                logger.warning(f"Insufficient data: {len(df)} samples, need at least {min_required_samples}")
                # Si es el último intento, devolver lo que tenemos
                if attempt == max_attempts - 1:
                    logger.warning("Returning incomplete data after maximum attempts")
                    return df
                await asyncio.sleep(2)

        return None

    async def subscribe_to_ticks(self, symbol, retry_attempts=3):
        """
        Subscribe to real-time price ticks

        Args:
            symbol: Trading symbol (e.g., "frxEURUSD")
            retry_attempts: Number of retry attempts
        """
        for attempt in range(retry_attempts):
            try:
                # Verificar estado de conexión
                if not await self.connector.check_connection():
                    logger.warning(f"Connection not available for tick subscription, attempt {attempt+1}/{retry_attempts}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                response = await self.connector.subscribe_to_ticks(symbol)

                if "error" in response:
                    logger.error(f"Error subscribing to ticks: {response['error']['message']}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                logger.info(f"Successfully subscribed to ticks for {symbol}")
                return response

            except Exception as e:
                logger.error(f"Error subscribing to ticks: {str(e)}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 * (attempt + 1))

        return None

    async def get_available_symbols(self, retry_attempts=3):
        """
        Get list of available trading symbols

        Args:
            retry_attempts: Number of retry attempts
        """
        for attempt in range(retry_attempts):
            try:
                # Verificar estado de conexión
                if not await self.connector.check_connection():
                    logger.warning(f"Connection not available for symbol list, attempt {attempt+1}/{retry_attempts}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                response = await self.connector.get_active_symbols()

                if "error" in response:
                    logger.error(f"Error fetching symbols: {response['error']['message']}")
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(2 * (attempt + 1))
                    continue

                symbols = []
                if "active_symbols" in response:
                    symbols = [symbol['symbol'] for symbol in response['active_symbols']]
                    logger.info(f"Found {len(symbols)} active trading symbols")

                return symbols

            except Exception as e:
                logger.error(f"Error fetching available symbols: {str(e)}")
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 * (attempt + 1))

        return None

    def clear_cache(self, symbol=None, older_than=3600):
        """
        Limpiar caché de datos

        Args:
            symbol: Símbolo específico a limpiar (None para todos)
            older_than: Eliminar entradas más antiguas que estos segundos
        """
        current_time = time.time()

        if symbol:
            # Limpiar sólo para el símbolo especificado
            keys_to_remove = [k for k in self.cache if k.startswith(f"{symbol}_")]
            for key in keys_to_remove:
                del self.cache[key]
                if symbol in self.last_fetch_time:
                    del self.last_fetch_time[symbol]
            logger.debug(f"Cleared cache for {symbol}")
        else:
            # Limpiar entradas antiguas para todos los símbolos
            for symbol in list(self.last_fetch_time.keys()):
                if current_time - self.last_fetch_time[symbol] > older_than:
                    # Eliminar todas las entradas de caché para este símbolo
                    keys_to_remove = [k for k in self.cache if k.startswith(f"{symbol}_")]
                    for key in keys_to_remove:
                        del self.cache[key]
                    del self.last_fetch_time[symbol]

            logger.debug("Cleared expired cache entries")