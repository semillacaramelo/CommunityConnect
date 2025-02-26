# Bot de Trading con ML para Deriv.com

## Descripción del Proyecto

Bot de trading automatizado que utiliza Machine Learning para operar en la plataforma Deriv.com, implementado en Python con una arquitectura modular y escalable, optimizado para operar en entornos live.

### Arquitectura Modular
```
deriv_bot/
├── data/                 # Módulos de datos y conexión API
├── strategy/            # Módulos de estrategia y ML
├── risk/               # Gestión de riesgo
├── execution/          # Ejecución de órdenes
├── monitor/            # Monitoreo y logging
└── utils/              # Utilidades generales
```

## Configuración para Entornos Live

### Requisitos del Sistema
- Python 3.11 o superior
- Dependencias especificadas en `requirements.txt`
- Cuenta en Deriv.com con tokens API

### Instalación y Configuración

#### 1. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

#### 2. Configuración del Entorno
Ejecuta el script de configuración:
```bash
python environment_setup.py
```

Para configurar VS Code al mismo tiempo:
```bash
python environment_setup.py --vscode
```

#### 3. Configuración de Tokens API de Deriv
- El script de configuración te guiará para ingresar:
  - Token API para cuenta Demo
  - Token API para cuenta Real
  - Otros parámetros de configuración

#### 4. Verificar la Conexión a la API
```bash
python test_api_connectivity.py
```

## Ejecución en Entornos Live

### Modo de Entrenamiento (sin trading)
```bash
python main.py --train-only
```

### Ejecutar en Modo Demo
```bash
python main.py --env demo
```

Opciones adicionales:
```bash
python main.py --env demo --symbol frxEURUSD --stake-amount 20 --train-interval 6
```

### Ejecutar en Modo Real
**IMPORTANTE**: El modo real utiliza fondos reales. Asegúrate de entender los riesgos.

1. Primero, confirma explícitamente que deseas usar el modo real editando `.env`:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Luego ejecuta:
   ```bash
   python main.py --env real
   ```

Opciones adicionales:
```bash
python main.py --env real --symbol frxEURUSD --stake-amount 10 --stop-loss 0.05
```

## Gestión de Modelos

### Reentrenamiento Automático
Durante la ejecución normal, el bot reentrena los modelos periódicamente:
```bash
python main.py --train-interval 4  # Reentrenar cada 4 horas
```

### Reentrenamiento Manual
```bash
python main.py --train-only
```

### Gestión de Archivos de Modelo
```bash
# Ver estadísticas de almacenamiento
python clean_models.py --action stats

# Realizar operaciones de limpieza y archivo
python clean_models.py --action both
```

## Configuración de VS Code
Para facilitar el desarrollo y ejecución con VS Code:
```bash
python environment_setup.py --vscode
```

Esto creará:
- Configuraciones de lanzamiento para diferentes modos
- Configuración del entorno de desarrollo
- Integración con el depurador

## Solución de Problemas en Entornos Live

### Error de Conexión a la API
- Verifica que tus tokens API sean correctos y no hayan expirado
- Ejecuta `python test_api_connectivity.py` para diagnosticar problemas
- Comprueba tu conexión a internet

### El Bot No Realiza Operaciones
- Verifica que la configuración de stake_amount sea adecuada
- Comprueba que los umbrales de predicción no sean demasiado restrictivos
- Revisa los logs para ver las predicciones y motivos de no-operación

### VS Code No Encuentra el Módulo deriv_bot
- Asegúrate de que la carpeta raíz del proyecto esté en Python Path
- Configura `python.analysis.extraPaths` en settings.json
- Reinicia VS Code después de cambiar la configuración

## Variables de Entorno Requeridas
- DERIV_API_TOKEN_DEMO
- DERIV_API_TOKEN_REAL
- DERIV_BOT_ENV
- DERIV_REAL_MODE_CONFIRMED (para modo real)
- APP_ID