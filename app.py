import streamlit as st
import sqlite3
import pandas as pd
import requests  # Necesario para la IP

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Elecciones Team BR200", page_icon="🏍️")

# Función para obtener la IP del votante


def get_remote_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except:
        return "IP no detectada"

# --- BASE DE DATOS ---


def init_db():
    conn = sqlite3.connect('elecciones_br200.db', check_same_thread=False)
    c = conn.cursor()
    # Añadimos la columna 'ip' a la tabla
    c.execute('''CREATE TABLE IF NOT EXISTS votos 
                 (votante TEXT, cargo TEXT, candidato TEXT, ip TEXT,
                 UNIQUE(votante, cargo))''')
    c.execute('CREATE TABLE IF NOT EXISTS config (llave TEXT, valor TEXT)')
    c.execute('SELECT valor FROM config WHERE llave = "ver_resultados"')
    if not c.fetchone():
        c.execute('INSERT INTO config VALUES ("ver_resultados", "NO")')
    conn.commit()
    return conn


conn = init_db()

# --- DATOS CANDIDATOS --- (Se mantiene igual)
candidatos = {
    "Presidente": ["Alex", "Diego"],
    "Vice-presidente": ["Emilio"],
    "Tesorera": ["Fabiola", "Leonardo"],
    "Ayudante de tesorería": ["Daniel Kavak", "Luis comisión", "Luis Ángel", "Anthony el capi"],
    "Secretaría": ["Alondra"],
    "Sargento de armas principal": ["Daniel Danher"],
    "Sargento de adiestramiento": ["Randhy", "Victor"],
    "Moderador": ["Jhonatan"],
    "Capitán de ruta": ["Kleiber"],
    "Centinelas": ["Christhian/Daniel"]
}

menu = st.sidebar.radio("Navegación", ["Votación", "Resultados 📊", "Admin 🔑"])

# --- 1. VOTACIÓN ---
if menu == "Votación":
    st.header("🇻🇪 Elecciones Team BR200 Aragua")
    st.image("moto_club.jpg", use_container_width=True)

    nombre = st.text_input("Nombre Completo:").strip().upper()
    ip_actual = get_remote_ip()  # Capturamos la IP aquí

    if nombre:
        with st.form("voto_form"):
            votos_user = {cargo: st.selectbox(
                f"{cargo}:", opciones) for cargo, opciones in candidatos.items()}
            if st.form_submit_button("REGISTRAR VOTO"):
                try:
                    c = conn.cursor()
                    for cargo, cand in votos_user.items():
                        c.execute("INSERT INTO votos VALUES (?, ?, ?, ?)",
                                  (nombre, cargo, cand, ip_actual))
                    conn.commit()
                    st.success(f"Voto registrado (IP: {ip_actual})")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ya has votado.")

# --- 2. RESULTADOS ---
elif menu == "Resultados 📊":
    st.title("📊 Escrutinio Final")
    c = conn.cursor()
    c.execute('SELECT valor FROM config WHERE llave = "ver_resultados"')
    if c.fetchone()[0] == "SI":
        df = pd.read_sql_query("SELECT * FROM votos", conn)

        if not df.empty:
            st.subheader("🏆 Ganadores por Cargo")
            # Lógica para encontrar al ganador (el que tiene más votos)
            for cargo in candidatos.keys():
                df_cargo = df[df['cargo'] == cargo]
                if not df_cargo.empty:
                    ganador = df_cargo['candidato'].value_counts().idxmax()
                    votos_ganador = df_cargo['candidato'].value_counts().max()
                    st.success(
                        f"**{cargo}**: {ganador} ({votos_ganador} votos)")

            st.divider()
            st.subheader("Detalle de Votación")
            for cargo in candidatos.keys():
                res_cargo = df[df['cargo'] ==
                               cargo]['candidato'].value_counts()
                st.write(f"**{cargo}**")
                st.bar_chart(res_cargo)
        else:
            st.info("Sin votos.")
    else:
        st.info("🔒 Resultados bloqueados por la Comisión.")

# --- 3. ADMIN (LISTA DE AUDITORÍA) ---
elif menu == "Admin 🔑":
    st.title("Panel de Auditoría")
    clave = st.text_input("Clave Maestra:", type="password")

    if clave == "aragua200":
        # Botones de control
        col1, col2 = st.columns(2)
        if col1.button("MOSTRAR RESULTADOS"):
            conn.execute(
                'UPDATE config SET valor = "SI" WHERE llave = "ver_resultados"')
            conn.commit()
        if col2.button("OCULTAR RESULTADOS"):
            conn.execute(
                'UPDATE config SET valor = "NO" WHERE llave = "ver_resultados"')
            conn.commit()

        st.divider()
        st.subheader("🕵️ Lista de Auditoría (IPs y Nombres)")
        df_audit = pd.read_sql_query(
            "SELECT DISTINCT votante, ip FROM votos", conn)
        st.dataframe(df_audit, use_container_width=True)

        # Alerta de duplicidad de IP
        duplicados = df_audit[df_audit.duplicated('ip', keep=False)]
        if not duplicados.empty:
            st.warning(
                "⚠️ Se detectaron diferentes nombres usando la misma IP:")
            st.write(duplicados)

