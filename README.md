# ¿Cuántos vendedores necesita realmente cada agencia?

**Proyecto final · Metodologías y herramientas para la analítica y visualización de datos**
Universidad Externado de Colombia · Maestría en Analítica de Datos para Contabilidad y Auditoría

**Autora:** Leidy Elizabeth Prieto Chaparro
**Docente:** Yefry Moncada

---

## La pregunta

Dado lo que cada agencia va a vender en 2026, **¿cuántos vendedores necesita?**

Dirigido a la Gerencia de Operaciones y a la Gerencia de Talento Humano. Se responde con sí o no.

## La fuente

Venta de tiquetes de Flota Sugamuxi, ERP SILOG, **enero 2022 – diciembre 2025**:
7.334.109 tiquetes, 66 agencias, 48 meses, $385.615 millones.

La base cruda **no está en este repositorio**. Lo que se publica es la tabla agregada a nivel
agencia-mes (`panel_agencias.csv`, 2.769 filas, 151 KB). La agregación elimina cédulas, nombres de
pasajeros y nombres de vendedores: en la tabla publicada **no queda ningún dato personal**.

Dos periodos vienen incompletos y están documentados por el proveedor del dato: noviembre de 2022
(días 11–20) y agosto de 2025 (días 1–10). Se verifican y se excluyen de la evaluación.

## Los cuatro niveles

| Nivel | Pregunta | Qué se encontró |
|---|---|---|
| Descriptiva | ¿Qué pasó? | 585 usuarios figuran vendiendo; **235 hacen el 90% de la venta** |
| Diagnóstica | ¿Por qué? | La productividad va de 48 a 2.135 tiquetes por vendedor al mes |
| Predictiva | ¿Qué va a pasar? | Pronóstico por agencia, mes a mes, para 2026: **1,66 millones de tiquetes (±6%)** |
| Prescriptiva | ¿Qué hago? | **63 personas están donde no se necesitan y faltan 36 donde sí** |

## Los modelos

| Modelo | Tipo | Resultado |
|---|---|---|
| Naive estacional | línea base | MAE 516 · la vara a superar |
| Regresión lineal | supervisado | MAE 436 · MASE 0,844 · **7 predicciones negativas** |
| **Bosque aleatorio** | supervisado | **MAE 416 · MASE 0,805 · ninguna imposible** ← el elegido |
| K-means (K=4) | **no supervisado** | agrupa las agencias y fija la vara de productividad de cada grupo |

**MASE 0,805** significa que el bosque comete el 80,5% del error del modelo tonto: le recorta
el error un 19,5%.

## Cómo se validó

- **Partición temporal**, no aleatoria: entrena 2023–2024, prueba 2025.
- **Ventana deslizante** con tres cortes: el modelo pasa de empatar con el tonto (MASE 1,00) a
  ganarle claramente (0,79) a medida que acumula historia.
- **La elección de K** se sustenta con codo y silueta, no a ojo.
- **El pronóstico se entrega con intervalo** (±6%, el peor error observado en 2025).

Los modelos ARIMA y los datos panel quedaron fuera del alcance del curso, así que la serie se
resolvió como **regresión supervisada con rezagos**, que es lo que la clase recomienda cuando hay
muchas series. La elección del rezago de 12 meses no es intuición: la autocorrelación da **+0,680
en el rezago 12** y prácticamente cero en los demás.

## Archivos

| Archivo | Qué es |
|---|---|
| `01_preparar_datos.py` | Resume los 48 archivos mensuales en la tabla agregada. Se corre una vez, fuera de este repositorio. |
| `panel_agencias.csv` | La tabla agregada y anonimizada. Es la fuente que lee el notebook. |
| `02_proyecto_final.ipynb` | Todo el análisis, de la fuente a la recomendación. 20 celdas de código y 42 de explicación. |

## Cómo correrlo

Abrir `02_proyecto_final.ipynb` en Google Colab y ejecutar todas las celdas. Corre completo en
**menos de 10 segundos** y descarga los datos por sí solo desde este repositorio.
