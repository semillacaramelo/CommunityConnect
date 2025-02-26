# Documentación del Bot de Trading ML para Deriv.com

## 1. Configuración para Entornos Live

### 1.1 Requisitos Previos
- Python 3.11 o superior
- Cuenta en Deriv.com con tokens API (demo y real)
- Dependencias instaladas mediante `pip install -r requirements.txt`

### 1.2 Configuración de Tokens API
Para utilizar el bot en entornos live es necesario configurar los tokens API:

1. Obtener tokens desde [Deriv API Token Page](https://app.deriv.com/account/api-token)
   - Para cuenta DEMO: Token con permisos "Read", "Trade", "Payments"
   - Para cuenta REAL: Token con permisos "Read", "Trade", "Payments"

2. Configurar el archivo `.env`:
   ```
   # Trading Environment (demo/real)
   DERIV_BOT_ENV=demo  # Cambiar a 'real' para operar con dinero real

   # Tokens API
   DERIV_API_TOKEN_DEMO=TU_TOKEN_DEMO_AQUÍ
   DERIV_API_TOKEN_REAL=TU_TOKEN_REAL_AQUÍ

   # Confirmación para modo real (medida de seguridad)
   DERIV_REAL_MODE_CONFIRMED=no  # Cambiar a 'yes' para permitir trading real

   # ID de Aplicación
   APP_ID=1089

   # Parámetros de entrenamiento
   SEQUENCE_LENGTH=30
   TRAINING_EPOCHS=50
   MODEL_SAVE_PATH=models
   ```

3. Verificar la conexión a la API:
   ```bash
   python test_api_connectivity.py
   ```

## 2. Ejecución del Bot en Entornos Live

### 2.1 Modo Demo (Práctica sin Riesgo)
Este modo permite operar sin utilizar fondos reales:

```bash
python main.py --env demo
```

Opciones adicionales:
```bash
python main.py --env demo --symbol frxEURUSD --stake-amount 20 --train-interval 6
```

### 2.2 Modo Real (Trading con Fondos Reales)
**IMPORTANTE**: Este modo utiliza fondos reales. Asegúrese de entender los riesgos asociados.

1. Primer paso (Medida de seguridad): Editar el archivo `.env` y establecer:
   ```
   DERIV_REAL_MODE_CONFIRMED=yes
   ```

2. Ejecutar el bot en modo real:
   ```bash
   python main.py --env real
   ```

Opciones adicionales:
```bash
python main.py --env real --symbol frxEURUSD --stake-amount 10 --stop-loss 0.05
```

## 3. Mantenimiento del Sistema

### 3.1 Reentrenamiento de Modelos

El sistema puede reentrenar los modelos automáticamente o manualmente:

1. **Reentrenamiento Automático**:
   Durante la ejecución normal, el bot reentrena los modelos según el intervalo configurado:
   ```bash
   python main.py --train-interval 4  # Reentrenar cada 4 horas
   ```

2. **Reentrenamiento Manual**:
   ```bash
   python main.py --train-only
   ```

### 3.2 Gestión de Modelos

Para administrar los archivos de modelos entrenados:

```bash
# Ver estadísticas de almacenamiento
python clean_models.py --action stats

# Archivar modelos antiguos (mantener los 5 más recientes)
python clean_models.py --action archive --keep 5

# Eliminar archivos archivados de más de 30 días
python clean_models.py --action clean --days 30

# Realizar ambas operaciones
python clean_models.py --action both
```

### 3.3 Variables de Entorno Requeridas

- `DERIV_API_TOKEN_DEMO`: Token API para cuenta de demostración
- `DERIV_API_TOKEN_REAL`: Token API para cuenta real
- `DERIV_BOT_ENV`: Entorno de trading (demo/real)
- `DERIV_REAL_MODE_CONFIRMED`: Confirmación para modo real (establecer a "yes")
- `APP_ID`: ID de aplicación Deriv

## 4. Solución de Problemas en Entornos Live

### 4.1 Errores de Conexión API
- Verificar que los tokens API sean correctos y no hayan expirado
- Ejecutar `python test_api_connectivity.py` para diagnosticar problemas
- Comprobar la conexión a internet

### 4.2 El Bot No Realiza Operaciones
- Verificar que la configuración de `stake_amount` sea adecuada
- Comprobar que los umbrales de predicción no sean demasiado restrictivos
- Revisar los logs en 'logs/trading_bot.log' para ver predicciones y motivos de no-operación

### 4.3 Errores en Modo Real
- Verificar que `DERIV_REAL_MODE_CONFIRMED=yes` en el archivo `.env`
- Confirmar que el token real tenga los permisos correctos
- Verificar suficientes fondos en la cuenta Deriv

### 4.4  Variables de entorno
- DERIV_API_TOKEN_DEMO
- DERIV_API_TOKEN_REAL
- DERIV_BOT_ENV
- APP_ID