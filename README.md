# ML Trading Bot for Deriv.com

## English Documentation

### Project Description
A modular Python-based trading bot for Deriv.com utilizing machine learning techniques for automated trading strategies.

Key Components:
- Deriv API integration
- Machine learning-powered trade decision making
- Modular architecture for extensibility
- Demo and real trading mode support

### Local Setup & Deployment
For detailed instructions on setting up and deploying this project on your local machine using Visual Studio Code, please refer to the [Setup Guide](SETUP_GUIDE.md).

The setup guide covers:
- System requirements
- Installation steps
- Environment configuration
- VS Code setup
- Running and debugging the bot
- Troubleshooting common issues

For VS Code specific setup instructions, see [VS Code Setup Guide](VSCODE_SETUP_EN.md).

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd deriv-ml-trading-bot

# Run the setup script (configures everything automatically)
python environment_setup.py --vscode

# Test API connectivity
python test_api_connectivity.py

# Train models
python main.py --train-only

# Run in demo mode
python main.py --env demo
```

---

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

## Configuración para Desarrollo Local

### Requisitos del Sistema
- Python 3.11 o superior
- Dependencias especificadas en `requirements.txt`
- Cuenta en Deriv.com con tokens API
- Visual Studio Code (recomendado para desarrollo)

### Instalación y Configuración

#### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/deriv-ml-trading-bot.git
cd deriv-ml-trading-bot
```

#### 2. Configurar el Entorno Virtual (Recomendado)
```bash
# Para Windows
python -m venv venv
venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

#### 4. Configuración del Archivo .env
Copia el archivo `.env.example` y renómbralo a `.env`:
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edita el archivo `.env` con tus tokens de API de Deriv:
```
DERIV_API_TOKEN_DEMO=tu_token_de_cuenta_demo
DERIV_API_TOKEN_REAL=tu_token_de_cuenta_real
DERIV_BOT_ENV=demo
APP_ID=1089
```

Para obtener los tokens API:
1. Inicia sesión en [Deriv.com](https://deriv.com)
2. Ve a Configuración de Cuenta > Seguridad y Límites > Tokens API
3. Genera tokens tanto para tu cuenta Demo como Real

#### 5. Configuración Asistida (Opcional)
Como alternativa, puedes utilizar el script de configuración automático:
```bash
python environment_setup.py
```

Para configurar VS Code al mismo tiempo:
```bash
python environment_setup.py --vscode
```

#### 6. Verificar la Conexión a la API
```bash
python test_api_connectivity.py
```

## Uso con Visual Studio Code

Para una configuración detallada de VS Code, consulta [VSCODE_SETUP.md](VSCODE_SETUP.md).

## Ejecución en Entornos de Desarrollo

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

## Solución de Problemas en Entornos de Desarrollo

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