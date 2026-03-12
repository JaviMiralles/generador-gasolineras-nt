import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from datetime import datetime

# Configuración básica de la página
st.set_page_config(page_title="Generador Gasolineras", layout="wide")

st.title("⛽ Generador: Gasolineras más baratas de España")
st.markdown("Sube el archivo `.xls` o `.csv` descargado del MITECO. El sistema generará el texto formateado y **tablas en imagen (JPG) descargables** con el Top 10 de la Península.")

# Función para dibujar la tabla como imagen
def generar_imagen_tabla(df_top, tipo_combustible):
    # Ajustamos el tamaño de la imagen (ancho, alto)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('off')
    
    # Preparar los datos
    datos = []
    col_precio = 'Precio gasolina 95 E5' if tipo_combustible == 'gasolina' else 'Precio gasóleo A'
    
    for i, (_, row) in enumerate(df_top.iterrows(), 1):
        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
        provincia = str(row['Provincia'])
        ubicacion = f"{localidad} ({provincia})"
        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN RÓTULO"
        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
        precio = f"{row[col_precio]:.3f} €/L"
        
        # Recortar textos muy largos para que quepan bien en la imagen
        if len(direccion) > 35: direccion = direccion[:32] + "..."
        if len(rotulo) > 20: rotulo = rotulo[:17] + "..."
        if len(ubicacion) > 25: ubicacion = ubicacion[:22] + "..."
        
        datos.append([f"#{i}", ubicacion, rotulo, direccion, precio])
        
    columnas = ["Pos.", "Ubicación (Provincia)", "Rótulo", "Dirección", "Precio"]
    
    # Crear la tabla
    tabla = ax.table(cellText=datos, colLabels=columnas, loc='center', cellLoc='center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(11)
    tabla.scale(1, 2) # Estirar un poco las celdas a lo alto
    
    # Colores y estilos para la cabecera y el precio
    color_cabecera = '#4CAF50' if tipo_combustible == 'gasolina' else '#2196F3'
    for (row, col), cell in tabla.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white', fontsize=12)
            cell.set_facecolor(color_cabecera)
        elif col == 4: # Columna de precio en negrita
            cell.set_text_props(weight='bold')
        
        # Dar más anchura a la columna de dirección
        if col == 3: cell.set_width(0.35)
        elif col == 0: cell.set_width(0.08)
            
    # Título de la imagen
    titulo = "Top 10 Gasolineras más baratas en la Península - Gasolina 95" if tipo_combustible == 'gasolina' else "Top 10 Gasolineras más baratas en la Península - Diésel"
    plt.title(titulo, fontsize=16, fontweight='bold', pad=10)
    
    # Guardar en buffer de memoria
    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=200)
    plt.close(fig)
    buf.seek(0)
    return buf

# Componente para subir el archivo
uploaded_file = st.file_uploader("Arrastra aquí tu archivo", type=['xls', 'xlsx', 'csv'])

if uploaded_file is not None:
    try:
        content = uploaded_file.read()
        df = None
        
        # Estrategia 1: Leer como CSV
        for encoding in ['utf-8', 'latin1', 'cp1252']:
            try:
                text = content.decode(encoding)
                lineas = text.split('\n')
                separador = ';' if len(lineas) > 3 and ';' in lineas[3] else ','
                df_temp = pd.read_csv(io.StringIO(text), skiprows=3, sep=separador, engine='python', quotechar='"', on_bad_lines='skip')
                df_temp.columns = df_temp.columns.str.strip()
                if 'Precio gasolina 95 E5' in df_temp.columns:
                    df = df_temp
                    break
            except Exception:
                continue
                
        # Estrategia 2: Leer como Excel binario
        if df is None:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, skiprows=3)
            df.columns = df.columns.str.strip()

        if df is None or 'Precio gasolina 95 E5' not in df.columns:
            st.error("❌ No se encontraron las columnas esperadas en el archivo.")
        else:
            with st.spinner("Procesando datos y generando listados e imágenes..."):
                def limpiar_precio(x):
                    if pd.isna(x) or x == '': return np.nan
                    x = str(x).replace(',', '.')
                    try: return float(x)
                    except: return np.nan

                # Limpieza
                df['Precio gasolina 95 E5'] = df['Precio gasolina 95 E5'].apply(limpiar_precio)
                df['Precio gasóleo A'] = df['Precio gasóleo A'].apply(limpiar_precio)
                df['Provincia'] = df['Provincia'].astype(str).str.title()
                provincias = sorted([p for p in df['Provincia'].unique() if p.lower() not in ['nan', '']])

                # 1. TOP 10 PENÍNSULA
                provincias_fuera = ['Ceuta', 'Melilla', 'Balears (Illes)', 'Santa Cruz De Tenerife', 'Palmas (Las)']
                df_peninsula = df[~df['Provincia'].isin(provincias_fuera)]

                top_10_gas = df_peninsula.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(10)
                top_10_die = df_peninsula.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(10)

                # Generar Imágenes
                img_gasolina = generar_imagen_tabla(top_10_gas, 'gasolina')
                img_diesel = generar_imagen_tabla(top_10_die, 'diesel')
                
                # Nombres de archivo con fecha de hoy
                fecha_hoy = datetime.now().strftime("%d-%m-%Y")
                nombre_img_gasolina = f"gasolineras-mas-baratas-gasolina-{fecha_hoy}.jpg"
                nombre_img_diesel = f"gasolineras-mas-baratas-diesel-{fecha_hoy}.jpg"

                # 2. GENERACIÓN DEL TEXTO HTML
                html_lines = []
                html_lines.append("<h2>Top 10: Las gasolineras más baratas de la Península</h2>")
                html_lines.append("<p>Listado de las 10 estaciones de servicio con los precios más bajos en la España peninsular (excluyendo Baleares, Canarias, Ceuta y Melilla).</p>")

                # Top 10 Gasolina Texto
                html_lines.append("<h3>⛽ Top 10 Gasolina 95 E5 más barata</h3>")
                html_lines.append("<ul>")
                for _, row in top_10_gas.iterrows():
                    provincia, localidad = str(row['Provincia']), str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
                    rotulo, direccion = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO", str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                    precio = f"{row['Precio gasolina 95 E5']:.3f}"
                    html_lines.append(f"    <li><strong>{localidad} ({provincia})</strong>: {rotulo}, {direccion} - <strong>{precio} &euro;/L</strong></li>")
                html_lines.append("</ul>")

                # Top 10 Diésel Texto
                html_lines.append("<h3>🛢️ Top 10 Diésel (Gasóleo A) más barato</h3>")
                html_lines.append("<ul>")
                for _, row in top_10_die.iterrows():
                    provincia, localidad = str(row['Provincia']), str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
                    rotulo, direccion = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO", str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                    precio = f"{row['Precio gasóleo A']:.3f}"
                    html_lines.append(f"    <li><strong>{localidad} ({provincia})</strong>: {rotulo}, {direccion} - <strong>{precio} &euro;/L</strong></li>")
                html_lines.append("</ul>")
                
                html_lines.append("<hr>")

                # Por provincias
                html_lines.append("<h2>Las gasolineras más baratas por provincia</h2>")
                html_lines.append("<p>En la web del Ministerio para la Transición Ecológica (MITECO), se puede consultar cuáles son las gasolineras más baratas en cada provincia. El siguiente listado muestra las estaciones con los precios más bajos en toda España.</p>")

                for prov in provincias:
                    html_lines.append(f"<h3>{prov}</h3>")
                    html_lines.append("<ul>")
                    df_prov = df[df['Provincia'] == prov]
                    
                    # Gasolina
                    for _, row in df_prov.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(2).iterrows():
                        loc, rot = str(row['Localidad']).title() if pd.notna(row['Localidad']) else "", str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO"
                        direc, pre = str(row['Dirección']).title() if pd.notna(row['Dirección']) else "", f"{row['Precio gasolina 95 E5']:.3f}"
                        html_lines.append(f"    <li>{loc}, {rot}, {direc}, {pre} &euro;/L (Gasolina 95)</li>")
                        
                    # Diesel
                    for _, row in df_prov.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(2).iterrows():
                        loc, rot = str(row['Localidad']).title() if pd.notna(row['Localidad']) else "", str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO"
                        direc, pre = str(row['Dirección']).title() if pd.notna(row['Dirección']) else "", f"{row['Precio gasóleo A']:.3f}"
                        html_lines.append(f"    <li>{loc}, {rot}, {direc}, {pre} &euro;/L (Diesel A)</li>")
                    html_lines.append("</ul>")

                html_final = "\n".join(html_lines)

            st.success("✅ ¡Listados e imágenes generadas con éxito!")
            
            # --- ZONA DE DESCARGA DE IMÁGENES ---
            st.subheader("🖼️ Descarga las imágenes del Top 10")
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(img_gasolina, caption="Top 10 Gasolina 95", use_container_width=True)
                st.download_button(label="📥 Descargar JPG Gasolina", data=img_gasolina, file_name=nombre_img_gasolina, mime="image/jpeg")
                
            with col2:
                st.image(img_diesel, caption="Top 10 Diésel", use_container_width=True)
                st.download_button(label="📥 Descargar JPG Diésel", data=img_diesel, file_name=nombre_img_diesel, mime="image/jpeg")

            # --- ZONA DE TEXTO ---
            st.markdown("---")
            st.info("👇 **Instrucciones:** Selecciona todo el texto de abajo con el ratón, cópialo y pégalo directamente en la vista visual de tu editor.")
            st.markdown(html_final, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Ha ocurrido un error inesperado al procesar el archivo: {e}")