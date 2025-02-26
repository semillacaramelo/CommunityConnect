"""
Asset Selection Module

Location: deriv_bot/utils/asset_selector.py

Purpose:
Manages asset selection logic including market hours,
asset availability, and selection strategies.

Dependencies:
- pandas: Data analysis
- deriv_bot.monitor.logger: Logging functionality
- deriv_bot.data.data_fetcher: Market data access

Interactions:
- Input: Market conditions and time data
- Output: Asset selection decisions
- Relations: Used by main loop for symbol selection

Author: Trading Bot Team
Last modified: 2024-02-26
"""

import logging
import datetime
from typing import List, Dict, Optional, Tuple
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

# Configurar logger
logger = logging.getLogger(__name__)

# Definir zonas horarias para los diferentes mercados
UTC = ZoneInfo("UTC")
NEW_YORK = ZoneInfo("America/New_York")
LONDON = ZoneInfo("Europe/London")
TOKYO = ZoneInfo("Asia/Tokyo")
SYDNEY = ZoneInfo("Australia/Sydney")

# Assets disponibles 24/7 (para fallback)
ALWAYS_AVAILABLE_ASSETS = [
    "frxEURUSD",  # EUR/USD
    "frxBTCUSD",  # Bitcoin/USD
    "R_10",       # Volatility Index 10
    "R_25",       # Volatility Index 25
    "R_50",       # Volatility Index 50
    "R_75",       # Volatility Index 75
    "R_100",      # Volatility Index 100
]

# Definir horarios de mercado para diferentes activos
# format: "symbol": [(día_inicio, hora_inicio, día_fin, hora_fin, zona_horaria), ...]
# día_inicio y día_fin: 0=domingo, 1=lunes, ..., 6=sábado
MARKET_HOURS: Dict[str, List[Tuple[int, time, int, time, ZoneInfo]]] = {
    # Forex majors - horarios aproximados
    "frxEURUSD": [(0, time(0, 0), 4, time(23, 59), UTC), (6, time(22, 0), 6, time(23, 59), UTC)],  # Domingo-Jueves completo, Viernes parcial
    "frxUSDJPY": [(0, time(0, 0), 4, time(23, 59), UTC), (6, time(22, 0), 6, time(23, 59), UTC)],
    "frxGBPUSD": [(0, time(0, 0), 4, time(23, 59), UTC), (6, time(22, 0), 6, time(23, 59), UTC)],

    # Indices bursátiles con horarios específicos
    "OTC_SPX": [(1, time(9, 30), 5, time(16, 0), NEW_YORK)],  # S&P 500 - Lunes a Viernes, horario NYSE
    "OTC_DJI": [(1, time(9, 30), 5, time(16, 0), NEW_YORK)],  # Dow Jones - Lunes a Viernes, horario NYSE
    "OTC_N225": [(1, time(9, 0), 5, time(15, 0), TOKYO)],     # Nikkei 225 - Lunes a Viernes, horario TSE
    "OTC_FTSE": [(1, time(8, 0), 5, time(16, 30), LONDON)],   # FTSE 100 - Lunes a Viernes, horario LSE

    # Materias primas
    "frxXAUUSD": [(0, time(23, 0), 5, time(22, 0), UTC)],     # Oro (Gold) - Domingo noche a Viernes

    # Criptomonedas (disponibles 24/7)
    "frxBTCUSD": [(0, time(0, 0), 6, time(23, 59), UTC)],     # Bitcoin - Todos los días
    "frxETHUSD": [(0, time(0, 0), 6, time(23, 59), UTC)],     # Ethereum - Todos los días

    # Índices de volatilidad (disponibles 24/7)
    "R_10": [(0, time(0, 0), 6, time(23, 59), UTC)],          # Volatility 10 Index - Todos los días
    "R_25": [(0, time(0, 0), 6, time(23, 59), UTC)],          # Volatility 25 Index - Todos los días
    "R_50": [(0, time(0, 0), 6, time(23, 59), UTC)],          # Volatility 50 Index - Todos los días
    "R_75": [(0, time(0, 0), 6, time(23, 59), UTC)],          # Volatility 75 Index - Todos los días
    "R_100": [(0, time(0, 0), 6, time(23, 59), UTC)],         # Volatility 100 Index - Todos los días
}

# Definir preferencias de activos por hora del día
# [(hora_inicio, hora_fin, [lista de activos en orden de preferencia])]
TIME_BASED_PREFERENCES = [
    # Madrugada/Mañana temprano (0:00-8:00 UTC): Mercados asiáticos más activos
    (time(0, 0), time(8, 0), ["frxUSDJPY", "OTC_N225", "frxEURUSD", "frxGBPUSD"]),

    # Mañana/Tarde (8:00-16:00 UTC): Mercados europeos más activos, apertura de US
    (time(8, 0), time(16, 0), ["frxEURUSD", "frxGBPUSD", "OTC_FTSE", "OTC_SPX", "OTC_DJI"]),

    # Tarde/Noche (16:00-24:00 UTC): Mercados americanos más activos
    (time(16, 0), time(23, 59), ["frxEURUSD", "OTC_SPX", "OTC_DJI", "frxXAUUSD", "frxGBPUSD"]),
]


class AssetSelector:
    """
    Clase para seleccionar activos basados en el horario actual y disponibilidad de mercado.
    """

    def __init__(self, data_fetcher=None, preferred_assets=None):
        """
        Inicializa el selector de activos.

        Args:
            data_fetcher: Instancia del fetcher de datos para verificar disponibilidad real
            preferred_assets: Lista opcional de activos preferidos por el usuario
        """
        self.data_fetcher = data_fetcher
        self.preferred_assets = preferred_assets or []
        self.available_assets_cache = {}
        self.cache_timestamp = None
        self.cache_validity = timedelta(minutes=15)  # Validez del caché

    def is_market_open(self, symbol: str, current_datetime: Optional[datetime] = None) -> bool:
        """
        Verifica si el mercado para un símbolo específico está abierto según su horario programado.
        Implementa lógica mejorada para mercados de acciones y considera zonas horarias.

        Args:
            symbol: Símbolo del activo a verificar
            current_datetime: Fecha y hora actual (UTC). Si es None, se usa la hora actual.

        Returns:
            bool: True si el mercado está abierto, False en caso contrario
        """
        if current_datetime is None:
            current_datetime = datetime.now(UTC)

        # Si el símbolo no está en el diccionario de horarios, asumimos que no está disponible
        if symbol not in MARKET_HOURS:
            logger.warning(f"No hay información de horario para el símbolo: {symbol}")
            return False

        # Obtener el día de la semana (0=lunes, 6=domingo) según el formato de Python
        weekday = current_datetime.weekday()

        # Convertir de formato Python (0=lunes, 6=domingo) a formato de calendario común (0=domingo, 6=sábado)
        calendar_weekday = (weekday + 1) % 7

        # Verificar cada rango de horario definido para el símbolo
        for start_day, start_time, end_day, end_time, timezone in MARKET_HOURS[symbol]:
            # Convertir la fecha y hora actual a la zona horaria del mercado
            market_datetime = current_datetime.astimezone(timezone)

            # Obtener hora actual en la zona horaria del mercado
            market_time = market_datetime.time()

            # Obtener día de la semana en la zona horaria del mercado (formato Python: 0=lunes)
            market_weekday = market_datetime.weekday()

            # Convertir a formato de calendario común (0=domingo, 6=sábado)
            market_calendar_weekday = (market_weekday + 1) % 7

            # Si es el mismo día, simplemente verificamos el rango de horas
            if start_day == end_day and market_calendar_weekday == start_day:
                if start_time <= market_time <= end_time:
                    return True

            # Si es un rango que cruza días
            elif start_day <= end_day:
                # Caso normal: ej. Lunes(1) a Viernes(5)
                if start_day <= market_calendar_weekday <= end_day:
                    # Primer día del rango: verificar que sea después de la hora de inicio
                    if market_calendar_weekday == start_day and market_time >= start_time:
                        return True
                    # Último día del rango: verificar que sea antes de la hora de fin
                    elif market_calendar_weekday == end_day and market_time <= end_time:
                        return True
                    # Días intermedios: mercado abierto todo el día
                    elif start_day < market_calendar_weekday < end_day:
                        return True
            else:
                # Caso que cruza fin de semana: ej. Viernes(5) a Lunes(1)
                if market_calendar_weekday >= start_day or market_calendar_weekday <= end_day:
                    # Primer día del rango
                    if market_calendar_weekday == start_day and market_time >= start_time:
                        return True
                    # Último día del rango
                    elif market_calendar_weekday == end_day and market_time <= end_time:
                        return True
                    # Días intermedios
                    elif (market_calendar_weekday > start_day or market_calendar_weekday < end_day):
                        return True

        return False

    def verify_asset_availability(self, symbol: str) -> bool:
        """
        Verifica si un activo está realmente disponible para trading.

        Args:
            symbol: Símbolo del activo a verificar

        Returns:
            bool: True si el activo está disponible, False en caso contrario
        """
        # Primero verificamos si el mercado debería estar abierto según el horario
        if not self.is_market_open(symbol):
            logger.debug(f"Mercado cerrado para {symbol} según horario programado")
            return False

        # Si tenemos un data_fetcher, verificamos la disponibilidad real mediante la API
        if self.data_fetcher:
            try:
                # Intentamos obtener el último tick para verificar disponibilidad
                # Esto podría ser reemplazado por una llamada más específica si está disponible
                is_available = self.data_fetcher.is_symbol_available(symbol)
                return is_available
            except Exception as e:
                logger.warning(f"Error al verificar disponibilidad de {symbol}: {e}")
                # Si hay un error, asumimos que no está disponible
                return False

        # Si no hay data_fetcher, asumimos que está disponible si el mercado está abierto
        return True

    def get_available_assets(self, force_refresh=False) -> List[str]:
        """
        Obtiene una lista de todos los activos disponibles en este momento.
        Utiliza caché para evitar consultas excesivas a la API.

        Args:
            force_refresh: Si es True, ignora el caché y consulta la disponibilidad actual

        Returns:
            List[str]: Lista de símbolos de activos disponibles
        """
        current_time = datetime.now(UTC)

        # Verificar si el caché es válido
        if (not force_refresh and 
            self.cache_timestamp and 
            current_time - self.cache_timestamp < self.cache_validity and
            self.available_assets_cache):
            return list(self.available_assets_cache)

        available_assets = []

        # Verificar cada activo en nuestro diccionario de horarios
        for symbol in MARKET_HOURS.keys():
            if self.verify_asset_availability(symbol):
                available_assets.append(symbol)

        # Actualizar caché
        self.available_assets_cache = available_assets
        self.cache_timestamp = current_time

        return available_assets

    def get_preferred_assets_by_time(self, current_time=None) -> List[str]:
        """
        Obtiene una lista de activos preferidos según la hora del día.

        Args:
            current_time: Hora actual (objeto time). Si es None, se usa la hora actual.

        Returns:
            List[str]: Lista de símbolos de activos en orden de preferencia
        """
        if current_time is None:
            current_time = datetime.now(UTC).time()

        # Buscar en las preferencias por hora
        for start_time, end_time, assets in TIME_BASED_PREFERENCES:
            # Manejar el caso especial cuando el rango cruza la medianoche
            if start_time <= end_time:
                if start_time <= current_time <= end_time:
                    return assets
            else:
                if current_time >= start_time or current_time <= end_time:
                    return assets

        # Si no encontramos ninguna coincidencia (no debería ocurrir), devolvemos la primera lista
        return TIME_BASED_PREFERENCES[0][2]

    def select_asset(self, preferred_asset=None) -> str:
        """
        Selecciona el mejor activo disponible para operar.

        Proceso de selección:
        1. Si se proporciona un activo preferido y está disponible, se usa ese
        2. Si hay una lista de activos preferidos por el usuario, se busca el primero disponible
        3. Se busca en la lista de activos preferidos según la hora actual
        4. Si ninguno está disponible, se usa un activo de la lista de fallback (24/7)

        Args:
            preferred_asset: Activo preferido específico para esta selección

        Returns:
            str: Símbolo del activo seleccionado
        """
        logger.info("Iniciando selección de activo")

        # Obtener activos disponibles
        available_assets = self.get_available_assets()

        if not available_assets:
            logger.warning("No se encontraron activos disponibles, usando fallback")
            # Si no hay activos disponibles según nuestra verificación,
            # asumimos que al menos los activos 24/7 están disponibles
            return ALWAYS_AVAILABLE_ASSETS[0]

        # Paso 1: Verificar el activo preferido específico
        if preferred_asset and preferred_asset in available_assets:
            logger.info(f"Usando activo preferido específico: {preferred_asset}")
            return preferred_asset

        # Paso 2: Verificar la lista de activos preferidos del usuario
        if self.preferred_assets:
            for asset in self.preferred_assets:
                if asset in available_assets:
                    logger.info(f"Usando activo preferido del usuario: {asset}")
                    return asset

        # Paso 3: Verificar activos preferidos según la hora actual
        time_based_preferences = self.get_preferred_assets_by_time()
        for asset in time_based_preferences:
            if asset in available_assets:
                logger.info(f"Usando activo basado en horario: {asset}")
                return asset

        # Paso 4: Fallback a activos disponibles 24/7
        for asset in ALWAYS_AVAILABLE_ASSETS:
            if asset in available_assets:
                logger.info(f"Usando activo fallback (24/7): {asset}")
                return asset

        # Si llegamos aquí, usamos el primer activo disponible
        selected_asset = available_assets[0]
        logger.info(f"Usando primer activo disponible: {selected_asset}")
        return selected_asset