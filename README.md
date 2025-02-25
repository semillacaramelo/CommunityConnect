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

## Estado Actual y Logros

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

### Variables de Entorno Requeridas
- DERIV_API_TOKEN_DEMO
- DERIV_API_TOKEN_REAL
- DERIV_BOT_ENV
- APP_ID

### Notas Importantes
- El proyecto usa Python 3.11
- TensorFlow está configurado para CPU
- Los logs se guardan en 'trading_bot.log'
- Las simulaciones exportan a 'simulation_results.csv'

## Estado de Pruebas
- ✓ Tests unitarios implementados
- ✓ Pruebas de integración API
- ✓ Simulaciones de trading verificadas
- ✓ Perfiles DEMO/REAL validados