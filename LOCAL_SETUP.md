# Configuración de Entorno Local para el Bot de Trading con ML

Este documento proporciona instrucciones detalladas para configurar el entorno de desarrollo local para el Bot de Trading con ML para Deriv.com, independientemente del IDE que utilices.

## Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Paso a Paso](#instalación-paso-a-paso)
3. [Configuración del Entorno](#configuración-del-entorno)
4. [Verificación de la Instalación](#verificación-de-la-instalación)
5. [Instalación de Herramientas Adicionales](#instalación-de-herramientas-adicionales)
6. [Solución de Problemas Comunes](#solución-de-problemas-comunes)

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.11 o superior**: [Descargar Python](https://www.python.org/downloads/)
  - Verifica la instalación con `python --version` o `python3 --version`
  - Asegúrate de que la opción "Añadir Python al PATH" esté marcada durante la instalación en Windows

- **Git**: [Descargar Git](https://git-scm.com/downloads)
  - Verifica la instalación con `git --version`

- **Cuenta en Deriv.com**: Necesitarás tokens API para las cuentas Demo y Real
  - [Registrarse en Deriv.com](https://deriv.com)

## Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/deriv-ml-trading-bot.git
cd deriv-ml-trading-bot
```

### 2. Configurar un Entorno Virtual

Es altamente recomendable usar un entorno virtual para aislar las dependencias de este proyecto:

#### En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### En macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

> **Nota**: Cuando veas el prefijo `(venv)` en tu terminal, significa que el entorno virtual está activo.

### 3. Instalar Dependencias

Una vez dentro del entorno virtual, instala todas las dependencias requeridas:

```bash
pip install -r requirements.txt
```

Esto instalará:
- python-deriv-api
- tensorflow
- scikit-learn
- pandas
- numpy
- python-dotenv
- websockets
- matplotlib

### 4. Probar la Instalación de Dependencias

Verifica que TensorFlow esté correctamente instalado:

```bash
python -c "import tensorflow as tf; print(tf.__version__)"
```

## Configuración del Entorno

### 1. Configuración Manual del Archivo .env

Copia el archivo de ejemplo y edítalo con tus propios valores:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edita el archivo `.env` con un editor de texto:

```
DERIV_API_TOKEN_DEMO=tu_token_de_cuenta_demo
DERIV_API_TOKEN_REAL=tu_token_de_cuenta_real
DERIV_BOT_ENV=demo
APP_ID=1089
```

### 2. Obtener Tokens API de Deriv

Para obtener tus tokens API:

1. Inicia sesión en [Deriv.com](https://deriv.com)
2. Ve a Configuración de Cuenta > Seguridad y Límites > Tokens API
3. Crea un nuevo token para tu cuenta Demo con los siguientes permisos:
   - Read
   - Trade
   - Payments
   - Admin
   - Trading information
4. Repite el proceso para tu cuenta Real

### 3. Configuración Automática (Alternativa)

Como alternativa a la configuración manual, puedes utilizar el script proporcionado:

```bash
python environment_setup.py
```

Este script te guiará a través de:
- Verificación de dependencias
- Configuración de variables de entorno
- Creación de directorios necesarios

## Verificación de la Instalación

### 1. Probar la Conexión a la API

Ejecuta el script de prueba para verificar que puedes conectarte correctamente a la API de Deriv:

```bash
python test_api_connectivity.py
```

Deberías ver un resultado satisfactorio con información sobre tu cuenta.

### 2. Probar la Recuperación de Datos

Prueba la recuperación de datos históricos:

```bash
python test_api_connectivity.py --mode demo --check-data
```

### 3. Ejecutar en Modo Demo Sin Trading

Para verificar que todo el sistema funciona correctamente sin realizar operaciones:

```bash
python main.py --env demo --dry-run
```

## Instalación de Herramientas Adicionales

### Herramientas de Análisis (Opcionales)

Para un análisis más detallado de los resultados y modelos, puedes instalar:

```bash
pip install seaborn jupyter
```

Esto te permitirá:
- Usar Jupyter Notebooks para análisis interactivo
- Crear visualizaciones más avanzadas con seaborn

## Solución de Problemas Comunes

### Error: ModuleNotFoundError

**Problema**: "No module named 'deriv_bot'"

**Solución**:
Asegúrate de estar ejecutando desde la carpeta raíz del proyecto o añade la carpeta raíz al PYTHONPATH:

```bash
# Windows
set PYTHONPATH=%PYTHONPATH%;%CD%

# macOS/Linux
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Error: Failed to connect to Deriv API

**Problema**: No se puede establecer conexión con la API de Deriv.

**Solución**:
1. Verifica que tus tokens API sean correctos en el archivo `.env`
2. Comprueba tu conexión a internet
3. Asegúrate de que la cuenta asociada al token no esté bloqueada

### Error: TensorFlow warnings about CUDA

**Problema**: Advertencias sobre CUDA no disponible al iniciar TensorFlow.

**Solución**:
Estas advertencias son normales si no tienes una GPU compatible con CUDA. El bot funcionará correctamente usando solo CPU para el entrenamiento y las predicciones.

### Error: Intel MKL o libiomp5md.dll conflicts

**Problema**: Conflictos con las bibliotecas MKL de Intel en Windows.

**Solución**:
```bash
pip uninstall numpy
pip install numpy==1.23.5
```

### Error: No available historical data

**Problema**: No se pueden recuperar datos históricos.

**Solución**:
1. Verifica que el símbolo solicitado exista y esté activo
2. Comprueba que el mercado esté abierto para ese símbolo
3. Intenta con un período de tiempo diferente
