# =====================================================================
#  PASO 1 · PREPARAR LOS DATOS
#  Proyecto final · ¿Cuántos vendedores necesita realmente cada agencia?
#  Leidy Elizabeth Prieto Chaparro
# =====================================================================
#
#  QUÉ HACE ESTE ARCHIVO
#  ---------------------
#  Lee los 48 archivos mensuales de tiquetes de Flota Sugamuxi
#  (7.334.109 filas, 280 MB) y los resume en UNA tabla pequeña:
#  una fila por agencia y por mes. El resultado son 2.769 filas
#  y 151 KB.
#
#  POR QUÉ SE HACE ASÍ, Y NO SE TRABAJA DIRECTO SOBRE LA BASE
#  ----------------------------------------------------------
#  Tres razones, y las tres hay que poder explicarlas:
#
#  1. ANONIMIZACIÓN. La base cruda trae cédula del pasajero, nombre
#     del pasajero y nombre del vendedor. Al agregar por agencia y mes
#     esos datos desaparecen: de una fila que dice "AGUAZUL, enero
#     2022, 3.027 tiquetes" no hay forma de llegar a una persona.
#     La sección 7 del enunciado exige anonimización real, y agregar
#     es la anonimización más limpia que existe.
#
#  2. TAMAÑO. GitHub no acepta archivos de más de 100 MB, y subir
#     280 MB de datos personales sería además una mala idea. Se sube
#     el resumen de 151 KB.
#
#  3. VELOCIDAD. El notebook trabaja sobre 2.769 filas y corre entero
#     en menos de 10 segundos en Google Colab.
#
#  CÓMO SE CORRE
#  -------------
#     pip install pandas pyarrow
#     python 01_preparar_datos.py
#
#  Toma unos 13 segundos y usa unos 640 MB de memoria. Se corre UNA
#  SOLA VEZ, en el computador donde está la base. No va a GitHub como
#  algo que otros ejecuten: va como evidencia de qué se anonimizó.
# =====================================================================

import glob          # para listar los 48 archivos de la carpeta
import pandas as pd  # para manejar las tablas


# ---------------------------------------------------------------------
# 1. DÓNDE ESTÁN LOS DATOS
# ---------------------------------------------------------------------
CARPETA = "parquet"              # carpeta con los tiquetes_AAAA-MM.parquet
SALIDA  = "panel_agencias.csv"   # el archivo que sí va a GitHub


# ---------------------------------------------------------------------
# 2. QUÉ NO ES UNA AGENCIA
# ---------------------------------------------------------------------
#  La columna "sucursal" del ERP trae 98 valores distintos, pero no
#  todos son agencias. Mezclados con las agencias reales vienen roles
#  operativos del sistema: INSPECTOR 1 a 9, RODAMIENTO, CHEQUEO,
#  RECAUDO, TELETIQUETE, APP ONLINE, XADMON, convenios y SIN DATO.
#
#  Verificado sobre los datos: esos 32 valores mueven apenas el 2,2%
#  del ingreso. Las 66 agencias reales concentran el 97,8%.
#
#  Dejarlos adentro contaminaría todo el análisis de personal, porque
#  un "INSPECTOR 3" no es una agencia con vendedores.
# ---------------------------------------------------------------------
NO_SON_AGENCIAS = ("INSPECTOR|RODAMIENTO|CHEQUEO|RECAUDO|TELETIQUETE|"
                   "APP ONLINE|XADMON|SIN DATO|CONVENIO|SUMINISTRO|OPTYMA|"
                   "PINBUS|RED BUS|SELVAVIAJES|ALAS LIBERTADORES|"
                   "PAPI QUIERO|PARQUE DEL AGUA")


# ---------------------------------------------------------------------
# 3. LA DEFINICIÓN CLAVE DEL PROYECTO: VENDEDOR EFECTIVO
# ---------------------------------------------------------------------
#  Un vendedor REGISTRADO es cualquier usuario que vendió al menos un
#  tiquete en el mes. Es lo que uno ve mirando el sistema.
#
#  Un vendedor EFECTIVO es uno de los que se reparten el 90% de las
#  ventas de ese mes en esa agencia.
#
#  Cómo se calcula, con un ejemplo. Si en una agencia en un mes vendieron
#  5 personas, con estos tiquetes:
#
#        Ana    600 tiquetes   ->  60% acumulado
#        Beto   250            ->  85%
#        Carlos  90            ->  94%   <- aqui se pasa del 90%
#        Diana   40            ->  98%
#        Eduardo 20            -> 100%
#
#  Registrados = 5. Efectivos = 3 (Ana, Beto y Carlos).
#  Los otros dos vendieron, pero su aporte es marginal.
#
#  La diferencia entre esos dos números es el hallazgo central del
#  proyecto: en 2025 hay 585 registrados y 235 efectivos.
#
#  Este cálculo hay que hacerlo AQUÍ y no en el notebook, porque
#  necesita el detalle tiquete por tiquete, que es justo lo que no
#  se publica.
# ---------------------------------------------------------------------
def vendedores_efectivos(columna_vendedor):
    # value_counts() cuenta cuántos tiquetes vendió cada persona
    ventas = columna_vendedor.value_counts().sort_values(ascending=False)
    # cumsum() va acumulando: 60%, 85%, 94%, 98%, 100%
    acumulado = ventas.cumsum() / ventas.sum()
    # cuántos están por debajo del 90%, más el que lo cruza
    return int((acumulado < 0.90).sum()) + 1


# ---------------------------------------------------------------------
# 4. PROCESAR MES POR MES
# ---------------------------------------------------------------------
#  Se leen los archivos de a uno y se resume cada mes antes de pasar al
#  siguiente. Así nunca hay 7,3 millones de filas en memoria al tiempo:
#  el pico son unos 640 MB en vez de varios gigas.
#
#  Solo se leen las 6 columnas que se necesitan. Las otras 27 —incluidas
#  cédula y nombre del pasajero— ni siquiera se cargan.
# ---------------------------------------------------------------------
COLUMNAS = ['fecha_venta', 'sucursal', 'vendedor', 'valor_silla',
            'anulado', 'trayecto']

resumenes = []

for archivo in sorted(glob.glob(f"{CARPETA}/tiquetes_*.parquet")):

    mes = pd.read_parquet(archivo, columns=COLUMNAS)

    # Quitar lo que no es una agencia
    mes = mes[~mes.sucursal.astype(str).str.contains(NO_SON_AGENCIAS)]

    # De la fecha completa (2022-01-10 23:01:09) sacar solo el mes: '2022-01'
    mes['periodo'] = mes.fecha_venta.dt.to_period('M').astype(str)

    # Marcar los que efectivamente viajaron
    mes['viajo'] = (mes.anulado == 'NO')

    # El resumen: una fila por agencia
    resumen = mes.groupby(['periodo', 'sucursal']).agg(
        tiquetes               = ('viajo', 'size'),        # todos los emitidos
        tiquetes_ok            = ('viajo', 'sum'),         # los que viajaron
        ingreso                = ('valor_silla', 'sum'),   # plata recaudada
        tarifa_mediana         = ('valor_silla', 'median'),# el tiquete tipico
        vendedores_registrados = ('vendedor', 'nunique'),  # cuantos figuran
        vendedores_efectivos   = ('vendedor', vendedores_efectivos),  # cuantos trabajan
        trayectos              = ('trayecto', 'nunique'),  # rutas distintas
    ).reset_index()

    # Los anulados salen por resta
    resumen['anulados'] = resumen.tiquetes - resumen.tiquetes_ok

    resumenes.append(resumen)
    print(f"  procesado {archivo}")


# ---------------------------------------------------------------------
# 5. UNIR LOS 48 RESÚMENES Y GUARDAR
# ---------------------------------------------------------------------
#  NOTA SOBRE LA TARIFA MEDIANA: se usa mediana y no promedio a
#  propósito. El archivo de origen advierte que hay unos 150 valores
#  atípicos por errores de digitación, algunos de miles de millones de
#  pesos. Un solo dato de esos desplaza el promedio de toda una agencia;
#  la mediana ni se entera. Es la lección de la clase sobre media y
#  mediana, aplicada aquí.
# ---------------------------------------------------------------------
panel = pd.concat(resumenes, ignore_index=True)
panel.to_csv(SALIDA, index=False)

print()
print(f"Listo: {SALIDA}")
print(f"  filas       : {len(panel):,}   (una por agencia y mes)")
print(f"  agencias    : {panel.sucursal.nunique()}")
print(f"  periodos    : {panel.periodo.nunique()}")
print(f"  tiquetes    : {panel.tiquetes.sum():,}")
print(f"  ingreso     : ${panel.ingreso.sum():,.0f}")
print()
print("Este archivo NO contiene ningun dato personal:")
print("  - no tiene cedulas de pasajeros")
print("  - no tiene nombres de pasajeros")
print("  - no tiene nombres de vendedores (solo CUANTOS hubo)")
print()
print("Sube SOLO este archivo a GitHub. La base cruda se queda aqui.")
