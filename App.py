import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import urllib.parse

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y TEMA CSS (Oscuro + Bordó + Cristal)
# ---------------------------------------------------------
st.set_page_config(
    page_title="MIX Ventasx",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Fondo principal y tipografía */
    .stApp {
        background-color: #0d0d11;
        color: #e0e0e0;
    }
    
    /* Efecto Glassmorphism para contenedores */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(128, 0, 32, 0.3) !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }

    /* Modificación de la barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #121218;
        border-right: 1px solid rgba(128, 0, 32, 0.4);
    }

    /* Botones primarios bordó */
    .stButton > button {
        background-color: #800020 !important;
        color: #ffffff !important;
        border: 1px solid #900C3F !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #900C3F !important;
        box-shadow: 0 0 12px rgba(144, 12, 63, 0.6) !important;
        border-color: #a52a2a !important;
    }

    /* Métrica Cards estilo cristal */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(128, 0, 32, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        backdrop-filter: blur(8px);
    }
    
    /* Títulos y Encabezados */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# GESTIÓN DE BASE DE DATOS LOCAL (SQLite)
# ---------------------------------------------------------
DB_FILE = "mix_ventas.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla Configuración
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Tabla Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'Vendedor',
            active INTEGER DEFAULT 1
        )
    """)
    
    # Tabla Pedidos / Ventas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            details TEXT NOT NULL,
            total_price REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'En Espera',
            seller_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla Gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            registered_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Valores por defecto
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('store_name', 'MIX Ventasx')")
    cursor.execute("INSERT OR IGNORE INTO users (username, password, name, role) VALUES ('admin', '2323', 'Administrador', 'Admin')")
    
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE DATOS
# ---------------------------------------------------------
def get_config(key):
    conn = get_db_connection()
    res = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    conn.close()
    return res['value'] if res else ""

def set_config(key, value):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# ESTADO DE SESIÓN Y AUTENTICACIÓN
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login_user(username, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ? AND active = 1", (username, password)).fetchone()
    conn.close()
    if user:
        st.session_state.logged_in = True
        st.session_state.user = dict(user)
        return True
    return False

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None

# ---------------------------------------------------------
# PÁGINA DE LOGIN
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: #800020;'>{get_config('store_name')}</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Iniciar Sesión</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username_input = st.text_input("Usuario")
            password_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar a la Plataforma", use_container_width=True)
            
            if submit:
                if login_user(username_input, password_input):
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
    st.stop()

# ---------------------------------------------------------
# ENCABEZADO SUPERIOR Y CONFIGURACIÓN DE MARCA
# ---------------------------------------------------------
current_store_name = get_config('store_name')

top_col1, top_col2, top_col3 = st.columns([1, 2, 1])
with top_col2:
    st.markdown(f"<h1 style='text-align: center; margin-bottom: 0px;'>{current_store_name}</h1>", unsafe_allow_html=True)

with top_col3:
    st.markdown(f"<p style='text-align: right; margin-bottom: 0px;'>👤 <b>{st.session_state.user['name']}</b> ({st.session_state.user['role']})</p>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión", key="logout_btn"):
        logout_user()
        st.rerun()

st.divider()

# ---------------------------------------------------------
# MENÚ NAVEGABLE (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.markdown("### 📌 Navegación")
menu_option = st.sidebar.radio(
    "Seleccionar apartado:",
    ["🛒 Ventas y Pedidos", "💸 Registrar Gastos", "📊 Dashboard Analítico", "👥 Gestión de Vendedores"]
)

# Edición rápida del Nombre del Punto de Venta desde la Sidebar
with st.sidebar.expander("⚙️ Configuración del Negocio"):
    new_store_name = st.text_input("Nombre de la Empresa", value=current_store_name)
    if st.button("Guardar Nombre"):
        set_config("store_name", new_store_name)
        st.success("Nombre actualizado")
        st.rerun()

# ---------------------------------------------------------
# APARTADO 1: VENTAS Y PEDIDOS (PANTALLA PRINCIPAL)
# ---------------------------------------------------------
if menu_option == "🛒 Ventas y Pedidos":
    st.subheader("🛒 Gestión de Ventas y Pedidos")
    
    # Formulario para Nuevo Pedido
    with st.expander("➕ Crear Nuevo Pedido"):
        with st.form("new_order_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                cust_name = st.text_input("Nombre del Cliente *")
                cust_phone = st.text_input("Teléfono / WhatsApp (ej: 5491122334455)")
                details = st.text_area("Detalle de los Productos / Servicio *")
            with col_b:
                total_price = st.number_input("Precio Final ($) *", min_value=0.0, step=100.0)
                deposit = st.number_input("Seña / Pago Inicial ($)", min_value=0.0, step=100.0)
            
            submit_order = st.form_submit_button("Registrar Pedido", use_container_width=True)
            if submit_order:
                if cust_name and details and total_price > 0:
                    status = "Cancelado" if deposit >= total_price else ("Señado" if deposit > 0 else "En Espera")
                    conn = get_db_connection()
                    conn.execute("""
                        INSERT INTO orders (customer_name, customer_phone, details, total_price, paid_amount, status, seller_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (cust_name, cust_phone, details, total_price, deposit, status, st.session_state.user['name']))
                    conn.commit()
                    conn.close()
                    st.success("¡Pedido creado exitosamente!")
                    st.rerun()
                else:
                    st.error("Por favor completa los campos obligatorios (*)")

    # Tabla y Listado de Pedidos
    conn = get_db_connection()
    orders_df = pd.read_sql_query("SELECT * FROM orders ORDER BY id DESC", conn)
    conn.close()

    if orders_df.empty:
        st.info("No hay pedidos registrados actualmente.")
    else:
        for _, order in orders_df.iterrows():
            remaining = order['total_price'] - order['paid_amount']
            status_color = "#28a745" if remaining <= 0 else ("#ffc107" if order['paid_amount'] > 0 else "#dc3545")
            
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 2])
                with c1:
                    st.markdown(f"### Pedido #{order['id']} - {order['customer_name']}")
                    st.write(f"**Detalle:** {order['details']}")
                    st.caption(f"Vendedor: {order['seller_name']} | Fecha: {order['created_at']}")
                
                with c2:
                    st.markdown(f"**Total:** ${order['total_price']:,.2f}")
                    st.markdown(f"**Pagado:** ${order['paid_amount']:,.2f}")
                    st.markdown(f"<span style='color:{status_color}; font-weight:bold;'>Saldo: ${remaining:,.2f}</span>", unsafe_allow_html=True)
                
                with c3:
                    st.progress(min(1.0, float(order['paid_amount'] / order['total_price'])) if order['total_price'] > 0 else 0)
                    st.caption(f"Estado: **{order['status']}**")
                
                with c4:
                    # Botón Registrar Pago de Saldo
                    if remaining > 0:
                        with st.popover("＋ Cobrar Saldo"):
                            add_pay = st.number_input(f"Monto a ingresar (Máx: ${remaining})", min_value=1.0, max_value=float(remaining), key=f"pay_{order['id']}")
                            if st.button("Confirmar Pago", key=f"btn_pay_{order['id']}"):
                                new_paid = order['paid_amount'] + add_pay
                                new_status = "Cancelado" if new_paid >= order['total_price'] else "Señado"
                                conn = get_db_connection()
                                conn.execute("UPDATE orders SET paid_amount = ?, status = ? WHERE id = ?", (new_paid, new_status, order['id']))
                                conn.commit()
                                conn.close()
                                st.rerun()
                    
                    # Botón WhatsApp Dinámico
                    if order['customer_phone']:
                        msg = f"Hola {order['customer_name']}! Te contactamos de {current_store_name} por tu pedido #{order['id']}. Total: ${order['total_price']} | Pagado: ${order['paid_amount']} | Saldo Pendiente: ${remaining}."
                        encoded_msg = urllib.parse.quote(msg)
                        wa_url = f"https://wa.me/{order['customer_phone']}?text={encoded_msg}"
                        st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; margin-top:5px; background-color:#25D366!important; border-color:#25D366!important;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
                    
                    # Comprobante PDF / Imprimible
                    receipt_html = f"""
                    <div style="font-family:Arial; padding:10px; color:#000; background:#fff; border-radius:5px;">
                        <h2 style="margin:0;">{current_store_name}</h2>
                        <p>Comprobante de Pedido #{order['id']}</p>
                        <hr>
                        <p><b>Cliente:</b> {order['customer_name']}</p>
                        <p><b>Detalle:</b> {order['details']}</p>
                        <p><b>Total:</b> ${order['total_price']}</p>
                        <p><b>Abonado:</b> ${order['paid_amount']}</p>
                        <p><b>Saldo Restante:</b> ${remaining}</p>
                        <hr>
                        <p style="font-size:12px;">Atendido por: {order['seller_name']}</p>
                    </div>
                    """
                    with st.popover("📄 Comprobante"):
                        st.components.v1.html(receipt_html, height=260)

            st.divider()

# ---------------------------------------------------------
# APARTADO 2: REGISTRAR GASTOS
# ---------------------------------------------------------
elif menu_option == "💸 Registrar Gastos":
    st.subheader("💸 Registro de Gastos y Salidas de Dinero")
    
    with st.form("expense_form"):
        exp_desc = st.text_input("Concepto / Descripción del Gasto *")
        exp_category = st.selectbox("Categoría", ["Insumos / Mercadería", "Servicios (Luz, Internet, etc.)", "Alquiler", "Sueldos / Comisiones", "Mantenimiento", "Otros"])
        exp_amount = st.number_input("Monto Saliente ($) *", min_value=1.0, step=100.0)
        
        submit_exp = st.form_submit_button("Cargar Gasto")
        if submit_exp:
            if exp_desc and exp_amount > 0:
                conn = get_db_connection()
                conn.execute("""
                    INSERT INTO expenses (description, amount, category, registered_by)
                    VALUES (?, ?, ?, ?)
                """, (exp_desc, exp_amount, exp_category, st.session_state.user['name']))
                conn.commit()
                conn.close()
                st.success("Gasto registrado correctamente.")
                st.rerun()

    st.markdown("### Historial de Gastos")
    conn = get_db_connection()
    exp_df = pd.read_sql_query("SELECT * FROM expenses ORDER BY id DESC", conn)
    conn.close()
    if not exp_df.empty:
        st.dataframe(exp_df, use_container_width=True)

# ---------------------------------------------------------
# APARTADO 3: DASHBOARD ANALÍTICO
# ---------------------------------------------------------
elif menu_option == "📊 Dashboard Analítico":
    st.subheader("📊 Balance General: Dinero Entrante vs. Saliente")
    
    conn = get_db_connection()
    orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
    expenses_df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()
    
    total_income = orders_df['paid_amount'].sum() if not orders_df.empty else 0.0
    total_pending = (orders_df['total_price'] - orders_df['paid_amount']).sum() if not orders_df.empty else 0.0
    total_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0.0
    net_balance = total_income - total_expenses
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Dinero Entrante (Cobrado)", f"${total_income:,.2f}")
    m2.metric("Saldos Pendientes a Cobrar", f"${total_pending:,.2f}")
    m3.metric("Dinero Saliente (Gastos)", f"${total_expenses:,.2f}")
    m4.metric("Balance Neto", f"${net_balance:,.2f}")
    
    st.divider()
    
    # Gráfico Comparativo Plotly
    fig = go.Figure(data=[
        go.Bar(name='Ingresos Cobrados', x=['Total Operativo'], y=[total_income], marker_color='#28a745'),
        go.Bar(name='Gastos Salientes', x=['Total Operativo'], y=[total_expenses], marker_color='#800020'),
        go.Bar(name='Saldos por Cobrar', x=['Total Operativo'], y=[total_pending], marker_color='#ffc107')
    ])
    fig.update_layout(
        title="Comparativa de Flujo de Caja",
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#ffffff")
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# APARTADO 4: GESTIÓN DE VENDEDORES / USUARIOS
# ---------------------------------------------------------
elif menu_option == "👥 Gestión de Vendedores":
    st.subheader("👥 Alta y Control de Vendedores")
    
    if st.session_state.user['role'] != 'Admin':
        st.warning("Solo los administradores pueden gestionar usuarios.")
    else:
        with st.expander("➕ Dar de Alta Nuevo Vendedor"):
            with st.form("new_user_form"):
                u_name = st.text_input("Nombre Completo *")
                u_user = st.text_input("Nombre de Usuario (Login) *")
                u_pass = st.text_input("Contraseña *", type="password")
                u_role = st.selectbox("Rol", ["Vendedor", "Admin"])
                
                submit_user = st.form_submit_button("Crear Usuario")
                if submit_user:
                    if u_name and u_user and u_pass:
                        try:
                            conn = get_db_connection()
                            conn.execute("""
                                INSERT INTO users (username, password, name, role)
                                VALUES (?, ?, ?, ?)
                            """, (u_user, u_pass, u_name, u_role))
                            conn.commit()
                            conn.close()
                            st.success(f"Usuario {u_user} creado con éxito.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("El nombre de usuario ya existe.")
        
        # Lista de Vendedores
        conn = get_db_connection()
        users_df = pd.read_sql_query("SELECT id, username, name, role, active FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)
