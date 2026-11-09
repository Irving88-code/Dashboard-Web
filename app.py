import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import io

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN TOKENS ─────────────────────────────────────────────────────────────
# Categorical palette — fixed order, CVD-safe (ΔE ≥ 8 adjacent pairs, OKLab)
CAT     = ["#2563EB", "#16A34A", "#DC2626", "#D97706", "#7C3AED", "#0891B2", "#DB2777", "#65A30D"]
SURFACE = "#FFFFFF"
BG      = "#F8FAFC"
GRID    = "#E2E8F0"
TEXT_1  = "#0F172A"
TEXT_2  = "#64748B"

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=SURFACE,
    font=dict(family="Inter, system-ui, sans-serif", color=TEXT_2, size=12),
    margin=dict(l=4, r=4, t=38, b=4),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        font=dict(size=11), bgcolor="rgba(0,0,0,0)", borderwidth=0,
    ),
    hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font_size=12, font_color=TEXT_1),
)

# ── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  section[data-testid="stSidebar"] {{ background: {SURFACE}; }}
  .stMainBlockContainer {{ background: {BG}; }}

  .kpi {{
    background: {SURFACE}; border: 1px solid {GRID}; border-radius: 10px;
    padding: 18px 20px 14px;
  }}
  .kpi-label {{
    font-size: 11px; font-weight: 600; letter-spacing: .06em;
    text-transform: uppercase; color: {TEXT_2}; margin-bottom: 6px;
  }}
  .kpi-value  {{ font-size: 26px; font-weight: 700; color: {TEXT_1}; line-height: 1.1; word-break: break-word; }}
  .kpi-value-sm {{ font-size: 18px; font-weight: 700; color: {TEXT_1}; line-height: 1.3; word-break: break-word; }}
  .kpi-sub    {{ font-size: 12px; color: {TEXT_2}; margin-top: 3px; }}
  .kpi-sub.up   {{ color: #15803D; }}
  .kpi-sub.down {{ color: #B91C1C; }}
</style>
""", unsafe_allow_html=True)


# ── DATOS DE EJEMPLO ─────────────────────────────────────────────────────────
@st.cache_data
def make_sample():
    rng   = np.random.default_rng(42)
    n     = 900
    start = datetime(2024, 1, 1)
    dates = [start + timedelta(days=int(d)) for d in rng.integers(0, 365, n)]

    catalog = {
        "Laptop Pro":          ("Electrónica",    18_000, 24_000),
        'Monitor 27"':         ("Electrónica",     4_500,  6_500),
        "Teclado Mecánico":    ("Accesorios",      1_200,  2_200),
        "Mouse Ergonómico":    ("Accesorios",        600,  1_100),
        "Auriculares BT":      ("Accesorios",      1_800,  3_200),
        'Tablet 10"':          ("Electrónica",     5_500,  8_000),
        "Cámara Web HD":       ("Accesorios",      1_100,  2_000),
        "SSD 1TB":             ("Almacenamiento",  1_400,  2_200),
        "HDD 4TB":             ("Almacenamiento",    900,  1_600),
        "USB-C Hub 7-en-1":    ("Accesorios",        800,  1_400),
    }
    regiones = ["Norte", "Sur", "Centro", "Occidente", "Oriente"]
    names    = list(catalog.keys())

    rows = []
    for i in range(n):
        name = names[rng.integers(0, len(names))]
        cat, pmin, pmax = catalog[name]
        precio = round(float(rng.uniform(pmin, pmax)), 2)
        qty    = int(rng.integers(1, 6))
        rows.append({
            "Fecha":     dates[i],
            "Producto":  name,
            "Categoría": cat,
            "Región":    regiones[rng.integers(0, len(regiones))],
            "Precio":    precio,
            "Cantidad":  qty,
            "Venta":     round(precio * qty, 2),
        })
    return pd.DataFrame(rows).sort_values("Fecha").reset_index(drop=True)


# ── CARGA DE ARCHIVO ──────────────────────────────────────────────────────────
def load_file(f):
    df = pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)
    for col in df.columns:
        if any(k in col.lower() for k in ("fecha", "date", "día", "dia")):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def find(df, *kws):
    for col in df.columns:
        if any(k in col.lower() for k in kws):
            return col
    return None


def period_delta(df, metric_col, date_col):
    if not date_col or df.empty or not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        return None, None
    dd = df.dropna(subset=[date_col])
    if len(dd) < 10:
        return None, None
    end  = dd[date_col].max()
    mid  = end - pd.Timedelta(days=30)
    beg  = mid - pd.Timedelta(days=30)
    cur  = dd[dd[date_col] > mid][metric_col].sum()
    prev = dd[(dd[date_col] > beg) & (dd[date_col] <= mid)][metric_col].sum()
    if prev == 0:
        return None, None
    pct = (cur - prev) / prev * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}% vs 30d ant.", pct >= 0


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Dashboard de Ventas")
    st.caption("Carga tu CSV o Excel para analizar tus datos")
    st.divider()

    uploaded = st.file_uploader(
        "Cargar archivo", type=["csv", "xlsx", "xls"],
        help="Columnas esperadas: Fecha, Producto, Categoría, Región, Precio, Cantidad, Venta"
    )
    is_sample = uploaded is None
    df_raw    = make_sample() if is_sample else load_file(uploaded)

    if is_sample:
        st.info("Sin archivo — mostrando datos de ejemplo.")
        csv_buf = io.BytesIO()
        df_raw.to_csv(csv_buf, index=False, encoding="utf-8-sig")
        st.download_button(
            "Descargar datos de ejemplo (.csv)",
            csv_buf.getvalue(), "ventas_ejemplo.csv", "text/csv",
            use_container_width=True,
        )

    st.divider()
    st.markdown("**Filtros**")

    date_col  = find(df_raw, "fecha", "date", "día", "dia")
    cat_col   = find(df_raw, "categ")
    reg_col   = find(df_raw, "región", "region", "reg")
    prod_col  = find(df_raw, "product", "producto")
    price_col = find(df_raw, "precio", "price")
    qty_col   = find(df_raw, "cantidad", "qty", "quant", "cant")
    sales_col = find(df_raw, "venta", "sale", "total", "ingreso", "importe")

    if sales_col is None and price_col and qty_col:
        df_raw = df_raw.copy()
        df_raw["Venta"] = df_raw[price_col] * df_raw[qty_col]
        sales_col = "Venta"

    df = df_raw.copy()

    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        mn = df[date_col].dropna().min().date()
        mx = df[date_col].dropna().max().date()
        rsel = st.date_input("Rango de fechas", (mn, mx), min_value=mn, max_value=mx)
        if isinstance(rsel, (list, tuple)) and len(rsel) == 2:
            df = df[(df[date_col].dt.date >= rsel[0]) & (df[date_col].dt.date <= rsel[1])]

    if cat_col:
        all_c = sorted(df_raw[cat_col].dropna().unique())
        sel_c = st.multiselect("Categoría", all_c, default=all_c)
        df    = df[df[cat_col].isin(sel_c)] if sel_c else df.iloc[:0]

    if reg_col:
        all_r = sorted(df_raw[reg_col].dropna().unique())
        sel_r = st.multiselect("Región", all_r, default=all_r)
        df    = df[df[reg_col].isin(sel_r)] if sel_r else df.iloc[:0]

    st.divider()
    st.markdown(
        '<div style="font-size:11px;color:#94A3B8;line-height:1.6">'
        "<b style='color:#64748B'>Stack técnico</b><br>"
        "Python · Streamlit · Plotly · Pandas · NumPy<br><br>"
        "<b style='color:#64748B'>Formato esperado</b><br>"
        "Fecha, Producto, Categoría,<br>Región, Precio, Cantidad, Venta"
        "</div>",
        unsafe_allow_html=True,
    )

# ── UTILIDADES ────────────────────────────────────────────────────────────────
def fmt_money(v):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"


def kpi_tile(label, value, sub=None, up=None, small=False):
    sub_html = ""
    if sub:
        cls = "up" if up is True else ("down" if up is False else "")
        arr = "▲ " if up is True else ("▼ " if up is False else "")
        sub_html = f'<div class="kpi-sub {cls}">{arr}{sub}</div>'
    val_cls = "kpi-value-sm" if small else "kpi-value"
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="{val_cls}">{value}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def title_cfg(text):
    return dict(text=text, font=dict(size=13, color=TEXT_1), x=0, xanchor="left")


def stylize(fig, **kw):
    fig.update_layout(**BASE_LAYOUT, **kw)
    fig.update_xaxes(
        showgrid=False, linecolor=GRID, tickcolor=GRID,
        tickfont=dict(size=11, color=TEXT_2),
    )
    fig.update_yaxes(
        gridcolor=GRID, gridwidth=1, zeroline=False,
        linecolor="rgba(0,0,0,0)", tickfont=dict(size=11, color=TEXT_2),
    )
    return fig


# ── CUERPO PRINCIPAL ──────────────────────────────────────────────────────────
st.markdown(
    '<h1 style="margin-bottom:2px">Dashboard de Ventas</h1>'
    f'<p style="color:{TEXT_2};font-size:14px;margin-bottom:16px">'
    "Carga tu CSV o Excel · filtra por fecha, categoría y región · exporta a Excel</p>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_v = df[sales_col].sum() if sales_col else 0
n_trans = len(df)
avg_p   = df[price_col].mean() if price_col else 0
top_p   = (
    df.groupby(prod_col)[sales_col].sum().idxmax()
    if (prod_col and sales_col) else "—"
)

delta_v, delta_v_up   = period_delta(df, sales_col, date_col) if sales_col else (None, None)
delta_n, delta_n_up   = (None, None)
delta_p, delta_p_up   = period_delta(df, price_col, date_col) if price_col else (None, None)

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_tile("Ventas Totales",  fmt_money(total_v), delta_v, delta_v_up)
with k2: kpi_tile("Transacciones",   f"{n_trans:,}",     None)
with k3: kpi_tile("Precio Promedio", fmt_money(avg_p),   delta_p, delta_p_up)
with k4: kpi_tile("Producto Líder",  str(top_p), small=True)

st.markdown("")

# ── FILA 1: Ventas por mes | Top productos ────────────────────────────────────
st.markdown("#### Tendencia y Productos")
c1, c2 = st.columns([3, 2])

with c1:
    with st.container(border=True):
        if date_col and sales_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
            m = (df.dropna(subset=[date_col])
                   .set_index(date_col)
                   .resample("ME")[sales_col].sum()
                   .reset_index()
                   .rename(columns={date_col: "Mes", sales_col: "V"}))
            m["lbl"] = m["Mes"].dt.strftime("%b %Y")

            fig = go.Figure(go.Scatter(
                x=m["lbl"], y=m["V"],
                mode="lines+markers",
                line=dict(color=CAT[0], width=2),
                marker=dict(size=8, color=CAT[0], line=dict(color=SURFACE, width=2)),
                fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
                hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
            ))
            stylize(fig, title=title_cfg("Ventas por Mes"), showlegend=False,
                    yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with c2:
    with st.container(border=True):
        if prod_col and sales_col:
            t8 = (df.groupby(prod_col)[sales_col].sum()
                    .nlargest(8).reset_index()
                    .rename(columns={prod_col: "P", sales_col: "V"})
                    .sort_values("V"))

            fig2 = go.Figure(go.Bar(
                x=t8["V"], y=t8["P"], orientation="h",
                marker=dict(color=CAT[0], line=dict(color="rgba(0,0,0,0)")),
                hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
            ))
            stylize(fig2, title=title_cfg("Top Productos por Venta"), showlegend=False,
                    xaxis_tickprefix="$", xaxis_tickformat=",.0f")
            fig2.update_xaxes(showgrid=True, gridcolor=GRID, linecolor="rgba(0,0,0,0)")
            fig2.update_yaxes(showgrid=False, tickfont=dict(size=10))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── FILA 2: Por categoría | Distribución de precios ──────────────────────────
st.markdown("#### Categorías y Precios")
c3, c4 = st.columns(2)

with c3:
    with st.container(border=True):
        if cat_col and sales_col:
            bc = (df.groupby(cat_col)[sales_col].sum().reset_index()
                    .rename(columns={cat_col: "C", sales_col: "V"})
                    .sort_values("V", ascending=False))
            colors_bc = [CAT[i % len(CAT)] for i in range(len(bc))]

            fig3 = go.Figure(go.Bar(
                x=bc["C"], y=bc["V"],
                marker=dict(color=colors_bc, line=dict(color="rgba(0,0,0,0)")),
                hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
            ))
            stylize(fig3, title=title_cfg("Ventas por Categoría"), showlegend=False,
                    yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with c4:
    with st.container(border=True):
        if cat_col and price_col:
            fig4 = go.Figure()
            for i, cat in enumerate(sorted(df[cat_col].dropna().unique())):
                vals = df[df[cat_col] == cat][price_col].dropna()
                fig4.add_trace(go.Box(
                    y=vals, name=cat,
                    marker_color=CAT[i % len(CAT)], line_width=1.5, boxpoints=False,
                    hovertemplate=f"<b>{cat}</b><br>$%{{y:,.0f}}<extra></extra>",
                ))
            stylize(fig4, title=title_cfg("Distribución de Precios por Categoría"),
                    showlegend=False,
                    yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

# ── FILA 3: Región ────────────────────────────────────────────────────────────
if reg_col and sales_col:
    st.markdown("#### Distribución Regional")
    c5, c6 = st.columns([2, 3])

    br = (df.groupby(reg_col)[sales_col].sum().reset_index()
            .rename(columns={reg_col: "R", sales_col: "V"})
            .sort_values("V", ascending=False))
    cr = [CAT[i % len(CAT)] for i in range(len(br))]

    with c5:
        with st.container(border=True):
            fig5 = go.Figure(go.Pie(
                labels=br["R"], values=br["V"],
                marker=dict(colors=cr, line=dict(color=SURFACE, width=2)),
                textinfo="percent+label", textfont_size=11,
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f} · %{percent}<extra></extra>",
            ))
            stylize(fig5, title=title_cfg("Participación por Región"), showlegend=False)
            st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    with c6:
        with st.container(border=True):
            if cat_col:
                pv = (df.groupby([reg_col, cat_col])[sales_col].sum().reset_index()
                        .rename(columns={reg_col: "R", cat_col: "C", sales_col: "V"}))
                fig6 = go.Figure()
                for i, cat in enumerate(sorted(pv["C"].unique())):
                    s = pv[pv["C"] == cat]
                    fig6.add_trace(go.Bar(
                        x=s["R"], y=s["V"], name=cat,
                        marker=dict(color=CAT[i % len(CAT)],
                                    line=dict(color=SURFACE, width=1)),
                        hovertemplate=f"<b>%{{x}} — {cat}</b><br>$%{{y:,.0f}}<extra></extra>",
                    ))
                stylize(fig6, title=title_cfg("Ventas por Región y Categoría"),
                        barmode="stack",
                        yaxis_tickprefix="$", yaxis_tickformat=",.0f")
                st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

# ── EVOLUCIÓN POR CATEGORÍA ───────────────────────────────────────────────────
if date_col and cat_col and sales_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
    st.markdown("#### Evolución Mensual por Categoría")
    with st.container(border=True):
        mc = (df.dropna(subset=[date_col])
                .groupby([pd.Grouper(key=date_col, freq="ME"), cat_col])[sales_col]
                .sum().reset_index()
                .rename(columns={date_col: "Mes", cat_col: "C", sales_col: "V"}))
        mc["lbl"] = mc["Mes"].dt.strftime("%b %Y")

        fig7 = go.Figure()
        for i, cat in enumerate(sorted(mc["C"].unique())):
            s = mc[mc["C"] == cat]
            fig7.add_trace(go.Scatter(
                x=s["lbl"], y=s["V"], name=cat,
                mode="lines+markers",
                line=dict(color=CAT[i % len(CAT)], width=2),
                marker=dict(size=6, color=CAT[i % len(CAT)],
                            line=dict(color=SURFACE, width=1.5)),
                hovertemplate=f"<b>{cat}</b> — %{{x}}<br>$%{{y:,.0f}}<extra></extra>",
            ))
        stylize(fig7, title=title_cfg("Evolución Mensual por Categoría"),
                yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})

# ── TABLA DE DATOS ────────────────────────────────────────────────────────────
st.markdown("#### Datos Detallados")
with st.expander("Ver tabla de datos", expanded=False):
    fmt_dict = {}
    if sales_col: fmt_dict[sales_col] = "${:,.2f}"
    if price_col: fmt_dict[price_col] = "${:,.2f}"
    st.dataframe(df.style.format(fmt_dict), use_container_width=True, height=380)

    xls = io.BytesIO()
    df.to_excel(xls, index=False, engine="openpyxl")
    xls.seek(0)
    st.download_button(
        "Descargar datos filtrados (.xlsx)", xls,
        "datos_filtrados.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
