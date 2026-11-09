# Dashboard de Ventas

Dashboard interactivo construido con Python y Streamlit para analizar el rendimiento comercial. Permite cargar archivos CSV o Excel propios, o explorar con datos de ejemplo incluidos.

---

## Características

- **KPIs principales**: ventas totales, transacciones, precio promedio y producto líder con variación vs. 30 días anteriores
- **Tendencia mensual**: gráfica de área con evolución de ingresos por mes
- **Top productos**: ranking horizontal de los 8 productos con mayor venta
- **Análisis por categoría**: ventas totales y distribución de precios (box plot)
- **Distribución regional**: participación por región (pie chart) y ventas apiladas por región y categoría
- **Evolución por categoría**: tendencia mensual desglosada por categoría
- **Tabla exportable**: vista de datos filtrados con descarga a Excel

## Stack técnico

| Librería | Versión |
|---|---|
| Python | 3.9+ |
| Streamlit | ≥ 1.28 |
| Plotly | ≥ 5.18 |
| Pandas | ≥ 2.2 |
| NumPy | ≥ 1.24 |
| openpyxl | ≥ 3.1 |

## Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/dashboard-ventas.git
cd dashboard-ventas

# 2. Crea y activa un entorno virtual
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Ejecuta la app
streamlit run app.py
```

## Uso

1. Abre la app en el navegador (por defecto `http://localhost:8501`)
2. Carga tu archivo **CSV** o **Excel** desde el panel lateral, o usa los datos de ejemplo
3. Aplica filtros de **fecha**, **categoría** y **región**
4. Explora las gráficas y descarga los datos filtrados en `.xlsx`

### Formato esperado del archivo

| Columna | Tipo | Descripción |
|---|---|---|
| Fecha | fecha | Fecha de la transacción |
| Producto | texto | Nombre del producto |
| Categoría | texto | Categoría del producto |
| Región | texto | Región de la venta |
| Precio | número | Precio unitario |
| Cantidad | entero | Unidades vendidas |
| Venta | número | Ingreso total (Precio × Cantidad) |

> Si tu archivo no incluye la columna `Venta`, se calcula automáticamente a partir de `Precio × Cantidad`.

## Estructura del proyecto

```
dashboard-ventas/
├── app.py               # Aplicación principal
├── requirements.txt     # Dependencias
├── .streamlit/
│   └── config.toml      # Configuración de tema
└── .gitignore
```
