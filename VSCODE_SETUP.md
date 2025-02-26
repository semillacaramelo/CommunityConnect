# Configuración y Uso del Bot de Trading en VS Code

Este documento proporciona instrucciones detalladas para configurar y ejecutar el Bot de Trading con ML para Deriv.com en Visual Studio Code.

## Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración Inicial](#configuración-inicial)
3. [Configuración de VS Code](#configuración-de-vs-code)
4. [Ejecución del Bot](#ejecución-del-bot)
5. [Depuración](#depuración)
6. [Flujo de Trabajo Recomendado](#flujo-de-trabajo-recomendado)
7. [Solución de Problemas Comunes](#solución-de-problemas-comunes)

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- [Python 3.11](https://www.python.org/downloads/) o superior
- [Visual Studio Code](https://code.visualstudio.com/download)
- Extensión de Python para VS Code
- Cuenta en [Deriv.com](https://deriv.com) con tokens API (demo y real)

## Configuración Inicial

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/deriv-ml-trading-bot.git
cd deriv-ml-trading-bot
```

### 2. Configurar el Entorno

#### 2.1 Configuración Automática
Ejecuta el script de configuración:

```bash
python environment_setup.py --vscode
```

#### 2.2 Configuración Manual del Entorno de Desarrollo

1. **Configurar Variables de Entorno**:
   Crea un archivo `.env` en la raíz del proyecto:
   ```
   DERIV_API_TOKEN_DEMO=TuTokenDemo
   DERIV_API_TOKEN_REAL=TuTokenReal
   DERIV_BOT_ENV=demo
   APP_ID=1089
   ```

2. **Configurar el Intérprete de Python**:
   - Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en macOS)
   - Escribe "Python: Select Interpreter"
   - Selecciona el intérprete de Python 3.11

3. **Verificar las Extensiones**:
   Asegúrate de tener instaladas:
   - Python
   - Pylance
   - Python Debugger

4. **Verificar la Configuración**:
   - Ejecuta `python test_api_connectivity.py --mode demo`
   - Confirma que la conexión es exitosa
   - Repite con `--mode real` si planeas usar modo real

Este comando:
- Crea/actualiza el archivo `.env` con tus configuraciones
- Verifica las dependencias de Python
- Crea archivos de configuración para VS Code
- Configura las carpetas necesarias

Alternativamente, puedes configurar cada componente manualmente:

#### Configuración Manual del Entorno

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Crear archivo .env**:
   - Copia `.env.example` a `.env`
   - Edita el archivo para incluir tus tokens API de Deriv

## Configuración de VS Code

### 1. Abrir el Proyecto

```bash
code .
```

### 2. Seleccionar el Intérprete de Python

1. Presiona `Ctrl+Shift+P` (Windows/Linux) o `Cmd+Shift+P` (macOS)
2. Escribe "Python: Select Interpreter"
3. Selecciona el intérprete de Python 3.11 o superior

### 3. Configuración de Lanzamiento

Si has ejecutado `environment_setup.py --vscode`, los archivos de configuración ya deberían estar creados. De lo contrario, crea manualmente los siguientes archivos:

#### .vscode/launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Check API Connection",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/test_api_connectivity.py",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Run Demo Mode",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--env", "demo"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Run Real Mode",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--env", "real"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Train Only",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "args": ["--train-only"],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Clean Models",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/clean_models.py",
            "args": ["--action", "both"],
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

#### .vscode/settings.json
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "autopep8",
    "python.formatting.autopep8Args": ["--max-line-length", "100"],
    "editor.formatOnSave": true,
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
```

## Ejecución del Bot

### Verificar Conexión a la API

Antes de ejecutar el bot completo, es recomendable verificar la conexión a la API:

1. En VS Code, abre la pestaña "Run and Debug" (Ctrl+Shift+D)
2. Selecciona la configuración "Check API Connection"
3. Presiona el botón de reproducción (F5)

Deberías ver un mensaje de confirmación si la conexión es exitosa.

### Entrenamiento de Modelos

Para entrenar los modelos sin realizar trading:

1. Selecciona la configuración "Train Only"
2. Presiona el botón de reproducción (F5)

#### Opciones Adicionales de Entrenamiento

Si deseas personalizar el entrenamiento, puedes modificar la configuración de lanzamiento añadiendo argumentos adicionales:

```json
"args": [
    "--train-only",
    "--model-types", "short_term", "medium_term",
    "--data-source", "both",
    "--save-data",
    "--sequence-length", "40",
    "--epochs", "100"
],
```

### Ejecución en Modo Demo

Para ejecutar el bot en modo demo (sin usar fondos reales):

1. Selecciona la configuración "Run Demo Mode"
2. Presiona el botón de reproducción (F5)

### Ejecución en Modo Real

**IMPORTANTE**: El modo real utiliza fondos reales. Asegúrate de entender los riesgos.

1. Primero, edita el archivo `.env` y establece:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Selecciona la configuración "Run Real Mode"
3. Presiona el botón de reproducción (F5)

### Limpieza de Archivos de Modelo

Para gestionar los archivos de modelo:

1. Selecciona la configuración "Clean Models"
2. Presiona el botón de reproducción (F5)

## Depuración

VS Code facilita la depuración del bot. Puedes:

1. Establecer puntos de interrupción haciendo clic en el margen izquierdo junto a los números de línea
2. Inspeccionar variables en la ventana de depuración
3. Ver la salida en la consola integrada

### Depuración Avanzada

Para habilitar logs más detallados, añade `--debug` a los argumentos:

```json
"args": ["--env", "demo", "--debug"],
```

## Flujo de Trabajo Recomendado

Para un desarrollo y operación eficientes, se recomienda el siguiente flujo de trabajo:

1. **Inicial**:
   - Verifica la conexión a la API
   - Entrena los modelos en modo "train-only"
   - Verifica los archivos de modelo generados

2. **Desarrollo**:
   - Realiza cambios en el código
   - Prueba la funcionalidad en modo demo
   - Utiliza puntos de interrupción para depurar problemas

3. **Operación**:
   - Ejecuta en modo demo hasta estar satisfecho con el rendimiento
   - Habilita el modo real con montos pequeños inicialmente
   - Monitorea regularmente los logs y el rendimiento

4. **Mantenimiento**:
   - Limpia los archivos de modelo periódicamente
   - Reentrana los modelos con nuevos datos
   - Actualiza las configuraciones según sea necesario

## Solución de Problemas Comunes

### El Módulo `deriv_bot` No Se Encuentra

**Problema**: VS Code no puede encontrar el módulo `deriv_bot`.

**Solución**:
1. Verifica que el setting `python.analysis.extraPaths` incluya `"${workspaceFolder}"`
2. Reinicia VS Code
3. Si persiste, asegúrate de que estás ejecutando desde la carpeta raíz del proyecto

### Error al Conectar con la API

**Problema**: No se puede establecer conexión con la API de Deriv.

**Solución**:
1. Verifica que tus tokens API en el archivo `.env` sean correctos
2. Comprueba tu conexión a internet
3. Asegúrate de que la cuenta asociada al token no esté bloqueada

### Errores Durante el Entrenamiento

**Problema**: El entrenamiento del modelo falla.

**Solución**:
1. Aumenta el nivel de log con `--debug`
2. Verifica que tengas suficientes datos históricos
3. Comprueba los requisitos de memoria para el entrenamiento
4. Intenta reducir el tamaño del modelo o la cantidad de datos

### El Bot No Realiza Operaciones

**Problema**: El bot se ejecuta pero no realiza operaciones de trading.

**Solución**:
1. Verifica los logs para ver las predicciones
2. Comprueba si las predicciones están por debajo del umbral mínimo
3. Revisa la configuración de gestión de riesgos
4. Asegúrate de que la cuenta tenga fondos suficientes
