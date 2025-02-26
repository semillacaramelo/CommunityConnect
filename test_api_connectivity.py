"""
Test script for verifying Deriv API connectivity
Following official documentation from:
- https://deriv-com.github.io/python-deriv-api/
- https://api.deriv.com/api-explorer
"""
import os
import asyncio
import json
import time
import argparse
from datetime import datetime
from deriv_bot.data.deriv_connector import DerivConnector
from deriv_bot.data.data_fetcher import DataFetcher
from deriv_bot.utils.config import Config
from deriv_bot.monitor.logger import setup_logger

logger = setup_logger('api_test')

async def test_api_connectivity(test_mode='demo', verbose=False, extended_test=False):
    """
    Test basic API connectivity and data fetching

    Args:
        test_mode: 'demo' or 'real' environment to test
        verbose: Show detailed output
        extended_test: Run more comprehensive tests
    """
    try:
        # Check environment variables
        print("\nVerifying environment variables:")
        env_vars = ['DERIV_API_TOKEN_DEMO', 'DERIV_API_TOKEN_REAL', 'DERIV_BOT_ENV', 'APP_ID']
        for var in env_vars:
            value = os.getenv(var)
            print(f"✓ {var}: {'Configured' if value else 'Not configured'}")

        # Configurar el entorno correcto para la prueba
        config = Config()
        if test_mode == 'real':
            if os.getenv('DERIV_API_TOKEN_REAL'):
                # Guardar valor actual para restaurar después
                original_env = config.get_environment()
                original_confirmed = os.getenv('DERIV_REAL_MODE_CONFIRMED')

                # Establecer temporalmente para prueba
                os.environ['DERIV_REAL_MODE_CONFIRMED'] = 'yes'
                if not config.set_environment('real'):
                    print("\n❗ No se pudo configurar el entorno REAL para pruebas")
                    print("  Verifique que DERIV_API_TOKEN_REAL esté configurado correctamente")
                    return
            else:
                print("\n❗ No se puede probar el entorno REAL: Falta DERIV_API_TOKEN_REAL")
                return
        else:
            # Asegurar que estamos en modo demo para la prueba
            config.set_environment('demo')

        print(f"\nProbando conexión a API en modo {config.get_environment().upper()}...")

        # Crear y probar el conector
        start_time = time.time()
        connector = DerivConnector(config)
        connected = await connector.connect()

        if not connected:
            print("❌ Falló la conexión a la API de Deriv")
            return

        connection_time = time.time() - start_time
        print(f"✓ Conexión exitosa a la API de Deriv ({connection_time:.2f}s)")

        # Probar obtención del tiempo del servidor
        print("\nVerificando tiempo del servidor...")
        time_response = await connector.get_server_time()

        if time_response and "time" in time_response:
            server_time = datetime.fromtimestamp(time_response["time"])
            local_time = datetime.now()
            time_diff = abs((local_time - server_time).total_seconds())
            print(f"✓ Tiempo del servidor: {server_time}")
            print(f"  Tiempo local: {local_time}")
            print(f"  Diferencia: {time_diff:.2f} segundos")
        else:
            print("❌ No se pudo obtener el tiempo del servidor")

        # Obtener símbolos disponibles
        print("\nObteniendo símbolos disponibles...")
        data_fetcher = DataFetcher(connector)
        symbols = await data_fetcher.get_available_symbols()

        if symbols:
            print(f"✓ Se encontraron {len(symbols)} símbolos de trading")
            print("Símbolos de ejemplo:", symbols[:5])
        else:
            print("❌ No se pudieron obtener símbolos de trading")

        # Probar obtención de datos históricos
        print("\nProbando obtención de datos históricos para EUR/USD...")
        historical_data = await data_fetcher.fetch_historical_data(
            symbol="frxEURUSD",
            interval=60,  # 1-minute candles
            count=10  # Just a few candles for testing
        )

        if historical_data is not None:
            print(f"✓ Datos históricos obtenidos correctamente ({len(historical_data)} velas)")
            print("\nMuestra de datos:")
            print(historical_data.head())
        else:
            print("❌ No se pudieron obtener datos históricos")

        # Prueba de suscripción a ticks
        print("\nProbando suscripción a ticks...")
        tick_response = await data_fetcher.subscribe_to_ticks("frxEURUSD")

        if tick_response and "error" not in tick_response:
            print("✓ Suscripción a ticks exitosa")
        else:
            print("❌ No se pudo suscribir a ticks")

        # Pruebas extendidas si se solicitan
        if extended_test:
            print("\n=== Ejecutando pruebas extendidas ===")

            # Prueba de carga: intentar obtener un conjunto grande de datos
            print("\nPrueba de carga: Obteniendo 1000 velas...")
            start_time = time.time()
            large_dataset = await data_fetcher.fetch_historical_data(
                symbol="frxEURUSD",
                interval=60,
                count=1000
            )
            load_time = time.time() - start_time

            if large_dataset is not None and len(large_dataset) > 900:
                print(f"✓ Conjunto grande de datos obtenido ({len(large_dataset)} velas en {load_time:.2f}s)")
            else:
                print(f"❌ Problemas al obtener conjunto grande de datos")
                if large_dataset is not None:
                    print(f"  Se solicitaron 1000 velas, se recibieron {len(large_dataset)}")

            # Prueba de reconexión
            print("\nPrueba de reconexión: Simulando desconexión...")
            await connector.close()
            reconnect_result = await connector.reconnect()

            if reconnect_result:
                print("✓ Reconexión exitosa")
            else:
                print("❌ Falló la reconexión")

            # Prueba de frecuencia de solicitudes
            print("\nPrueba de frecuencia de solicitudes: 5 solicitudes rápidas...")
            for i in range(5):
                start_req = time.time()
                mini_data = await data_fetcher.fetch_historical_data(
                    symbol="frxEURUSD",
                    interval=60,
                    count=5
                )
                req_time = time.time() - start_req
                status = "✓" if mini_data is not None else "❌"
                print(f"  Solicitud {i+1}: {status} ({req_time:.2f}s)")

            print("\nPruebas extendidas completadas")

        # Limpiar
        await connector.close()
        print("\n✓ Conexión cerrada correctamente")

        # Si cambiamos al modo real solo para la prueba, restauramos
        if test_mode == 'real' and original_env != 'real':
            config.set_environment(original_env)
            if original_confirmed:
                os.environ['DERIV_REAL_MODE_CONFIRMED'] = original_confirmed
            else:
                os.environ.pop('DERIV_REAL_MODE_CONFIRMED', None)
            print(f"\nEntorno restaurado a {config.get_environment().upper()}")

        # Resumen
        print("\n=== Resumen de la prueba ===")
        print(f"✓ Entorno: {config.get_environment().upper()}")
        print(f"✓ Conexión a API: {'Exitosa' if connected else 'Fallida'}")
        print(f"✓ Obtención de símbolos: {'Exitosa' if symbols else 'Fallida'}")
        print(f"✓ Datos históricos: {'Exitosos' if historical_data is not None else 'Fallidos'}")
        print(f"✓ Suscripción a ticks: {'Exitosa' if tick_response and 'error' not in tick_response else 'Fallida'}")

    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        logger.exception("Error during API test")

def main():
    """Main function with command line parser"""
    parser = argparse.ArgumentParser(description="Test Deriv API connectivity")
    parser.add_argument("--mode", choices=["demo", "real"], default="demo",
                        help="Test mode: demo (default) or real environment")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show verbose output")
    parser.add_argument("--extended", "-e", action="store_true",
                        help="Run extended tests")

    args = parser.parse_args()

    print("Iniciando prueba de conectividad con la API de Deriv...")
    print("===============================================")
    print(f"Modo: {args.mode.upper()}")

    asyncio.run(test_api_connectivity(
        test_mode=args.mode,
        verbose=args.verbose,
        extended_test=args.extended
    ))

if __name__ == "__main__":
    main()