# Bot de Trading con ML para Deriv.com

## Descripción del Proyecto

### Objetivo
Desarrollo de un bot de trading automatizado que utiliza Machine Learning para operar en la plataforma Deriv.com, implementado en Python con una arquitectura modular y escalable.

### Arquitectura Modular
El proyecto está estructurado en los siguientes módulos principales:

```
deriv_bot/
├── data/                 # Módulos de datos y conexión API
├── strategy/            # Módulos de estrategia y ML
├── risk/               # Gestión de riesgo
├── execution/          # Ejecución de órdenes
├── monitor/            # Monitoreo y logging
└── utils/              # Utilidades generales
```

### Funcionalidades Implementadas

1. **Conexión API (✓ Completado)**
   - Conexión WebSocket segura con Deriv API
   - Manejo de autenticación con tokens
   - Reconexión automática y manejo de errores

2. **Obtención de Datos (✓ Completado)**
   - Datos históricos de precios
   - Streaming de ticks en tiempo real
   - Validación y procesamiento de datos

3. **Procesamiento de Datos (✓ Completado)**
   - Cálculo de indicadores técnicos
   - Preparación de secuencias para ML
   - Normalización de datos

4. **Modelo ML (✓ Fase Inicial)**
   - Arquitectura LSTM básica
   - Entrenamiento con datos históricos
   - Predicción de movimientos de precios

5. **Gestión de Riesgo (✓ Completado)**
   - Validación de operaciones
   - Control de exposición
   - Límites de pérdidas
   - Perfiles DEMO/REAL implementados

6. **Simulación de Trading (✓ Completado)**
   - Ejecución simulada de órdenes
   - Tracking de rendimiento
   - Exportación de resultados
   - Perfil DEMO agresivo para pruebas

## Configuración y Ejecución

### Requisitos del Sistema
- Python 3.11 o superior
- Dependencias especificadas en `requirements.txt`
- Cuenta en Deriv.com con tokens API

### Instalación y Configuración

#### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/deriv-ml-trading-bot.git
cd deriv-ml-trading-bot
```

#### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### 3. Configurar el Entorno
Ejecuta el script de configuración:
```bash
python environment_setup.py
```

Para configurar VS Code al mismo tiempo:
```bash
python environment_setup.py --vscode
```

#### 4. Configuración de Tokens API de Deriv
El script de configuración te guiará para ingresar:
- Token API para cuenta Demo
- Token API para cuenta Real
- Otros parámetros de configuración

### Ejecución del Bot

#### Verificar la Conexión a la API
```bash
python test_api_connectivity.py
```

#### Modo de Entrenamiento (sin trading)
```bash
python main.py --train-only
```

#### Ejecutar en Modo Demo
```bash
python main.py --env demo
```

#### Ejecutar en Modo Real
**IMPORTANTE**: El modo real utiliza fondos reales. Asegúrate de entender los riesgos.

1. Primero, confirma explícitamente que deseas usar el modo real editando `.env`:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Luego ejecuta:
   ```bash
   python main.py --env real
   ```

#### Opciones Adicionales
```bash
python main.py --symbol frxEURUSD --stake-amount 20 --train-interval 6
```

### Gestión de Archivos de Modelo
El sistema acumula archivos de modelos entrenados que pueden ocupar espacio de almacenamiento. Usa este script para administrarlos:

#### Ver Estadísticas de Almacenamiento
```bash
python clean_models.py --action stats
```

#### Archivar Modelos Antiguos
```bash
python clean_models.py --action archive --keep 5
```

#### Eliminar Archivos Archivados Antiguos
```bash
python clean_models.py --action clean --days 30
```

#### Realizar Ambas Operaciones
```bash
python clean_models.py --action both
```

#### Opciones Adicionales
- `--dry-run`: Muestra qué archivos serían afectados sin realizar cambios
- `--model-type`: Filtra por tipo de modelo (ej: short_term, long_term)
- `--verbose`: Muestra información detallada de cada archivo

## Configuración para VS Code

### 1. Configuración Automática
La forma más fácil es usar:
```bash
python environment_setup.py --vscode
```

Esto creará automáticamente los archivos de configuración necesarios.

### 2. Configuración Manual (Alternativa)

#### Configuración del Entorno de Desarrollo

1. **Abrir el Proyecto en VS Code**
   ```bash
   code .
   ```

2. **Seleccionar el Intérprete de Python**
   - Presiona `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac)
   - Escribe "Python: Select Interpreter"
   - Selecciona el intérprete de Python 3.11 o superior

3. **Configurar Terminal Integrada**
   - En VS Code, abre una terminal integrada (``Ctrl+` ``)
   - Asegúrate de que la terminal tiene acceso a tu entorno Python

#### Crear archivos de configuración de VS Code

1. **Crear directorio `.vscode`**
   ```bash
   mkdir -p .vscode
   ```

2. **Crear archivo `launch.json`**
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Check API Connection",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/test_api_connectivity.py",
               "console": "integratedTerminal"
           },
           {
               "name": "Run Demo Mode",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/main.py",
               "args": ["--env", "demo"],
               "console": "integratedTerminal"
           },
           {
               "name": "Run Real Mode",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/main.py",
               "args": ["--env", "real"],
               "console": "integratedTerminal"
           },
           {
               "name": "Train Only",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/main.py",
               "args": ["--train-only"],
               "console": "integratedTerminal"
           }
       ]
   }
   ```

3. **Configurar `settings.json`**
   ```json
   {
       "python.linting.enabled": true,
       "python.linting.pylintEnabled": true,
       "python.formatting.provider": "autopep8",
       "python.formatting.autopep8Args": ["--max-line-length", "100"],
       "editor.formatOnSave": true,
       "python.analysis.extraPaths": ["${workspaceFolder}"]
   }
   ```

## Cambio entre Cuenta Demo y Real

### Método 1: Usando el Archivo .env

1. Edita el archivo `.env` y cambia las variables:
   ```
   DERIV_BOT_ENV=demo  # Para modo demo
   DERIV_BOT_ENV=real  # Para modo real

   # Para modo real, también necesitas confirmar explícitamente:
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Asegúrate de que tengas configurado el token correcto para cada modo:
   ```
   DERIV_API_TOKEN_DEMO=tu_token_demo
   DERIV_API_TOKEN_REAL=tu_token_real
   ```

### Método 2: Usando el Parámetro de Línea de Comandos

Simplemente especifica el entorno con el parámetro `--env`:
```bash
python main.py --env demo  # Para modo demo
python main.py --env real  # Para modo real (requiere DERIV_REAL_MODE_CONFIRMED=yes)
```

### Método 3: Mediante la Configuración de VS Code

Utiliza las configuraciones de lanzamiento descritas anteriormente para cambiar rápidamente entre modos.

### Consideraciones de Seguridad

- **IMPORTANTE**: El modo real utiliza fondos reales. Verifica cuidadosamente la configuración antes de ejecutar.
- Se mostrará una advertencia cuando operes en modo real.
- Se requiere confirmación explícita mediante `DERIV_REAL_MODE_CONFIRMED=yes`.
- Considera usar montos de operación pequeños para pruebas en modo real.

## Reentrenamiento de Modelos

El sistema puede reentrenar los modelos automáticamente o manualmente.

### Reentrenamiento Automático

Durante la ejecución normal, el bot reentrena los modelos periódicamente según el intervalo configurado:
```bash
python main.py --train-interval 4  # Reentrenar cada 4 horas
```

### Reentrenamiento Manual

Para reentrenar manualmente los modelos:
```bash
python main.py --train-only
```

### Gestión de Modelos Antiguos

Los modelos antiguos se archivan automáticamente para conservar espacio. Para gestionar manualmente:
```bash
python clean_models.py --action both
```

## Notas Técnicas
- El proyecto usa Python 3.11
- TensorFlow está configurado para CPU
- Los logs se guardan en 'logs/trading_bot.log'
- Las simulaciones exportan a 'simulation_results.csv'
- Los modelos se guardan en 'models/' y se archivan en 'model_archive/'

## Variables de Entorno Requeridas
- DERIV_API_TOKEN_DEMO
- DERIV_API_TOKEN_REAL
- DERIV_BOT_ENV
- DERIV_REAL_MODE_CONFIRMED (para modo real)
- APP_ID

## Solución de Problemas

### Error de Conexión a la API
- Verifica que tus tokens API sean correctos y no hayan expirado
- Ejecuta `python test_api_connectivity.py` para diagnosticar problemas
- Comprueba tu conexión a internet

### Errores al Entrenar el Modelo
- Asegúrate de que tienes suficientes datos históricos
- Verifica que tensorflow esté instalado correctamente
- Aumenta el número de épocas si el modelo no converge

### El Bot No Realiza Operaciones
- Verifica que la configuración de stake_amount sea adecuada
- Comprueba que los umbrales de predicción no sean demasiado restrictivos
- Revisa los logs para ver las predicciones y motivos de no-operación

### VS Code No Encuentra el Módulo deriv_bot
- Asegúrate de que la carpeta raíz del proyecto esté en Python Path
- Configura `python.analysis.extraPaths` en settings.json
- Reinicia VS Code después de cambiar la configuración

## Estado de Pruebas
- ✓ Tests unitarios implementados
- ✓ Pruebas de integración API
- ✓ Simulaciones de trading verificadas
- ✓ Perfiles DEMO/REAL validados

### Módulos Verificados
1. ✓ Conexión estable a Deriv API
2. ✓ Obtención y procesamiento de datos
3. ✓ Implementación básica de ML
4. ✓ Sistema de simulación funcional
5. ✓ Gestión de riesgo implementada
6. ✓ Perfiles DEMO/REAL configurados

### Resultados de Simulación
- Sistema capaz de ejecutar el ciclo completo de trading
- Registro detallado de operaciones en CSV
- Métricas de rendimiento implementadas:
  - Win rate
  - Profit/Loss por operación
  - Seguimiento de predicciones vs resultados reales
  - Evaluación de confianza de predicciones

## Próximos Pasos

### Prioridades Inmediatas
1. **Optimización del Modelo ML**
   - Ajuste fino de hiperparámetros
   - Evaluación de distintos horizontes de predicción
   - Mejora de features técnicos

2. **Panel de Control en Tiempo Real**
   - Desarrollo de interfaz web
   - Visualización de métricas clave
   - Control de parámetros de trading

3. **Backtesting Avanzado**
   - Implementación de múltiples pares de divisas
   - Análisis de correlaciones
   - Optimización de parámetros

### Mejoras Futuras Propuestas

1. **Sistema de Notificaciones**
   - Integración con Twilio para alertas SMS
   - Notificaciones de eventos críticos
   - Alertas de performance y riesgo

2. **Gestión de Riesgo Adaptativa**
   - Ajuste dinámico de parámetros
   - Machine Learning para gestión de riesgo
   - Optimización de portfolio

3. **Análisis de Mercado Avanzado**
   - Integración de análisis de sentimiento
   - Indicadores económicos en tiempo real
   - Correlaciones entre mercados

4. **Automatización y Escalabilidad**
   - Auto-optimización de parámetros
   - Balanceo de carga
   - Recuperación automática de errores