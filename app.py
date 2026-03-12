import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

# Configuración básica de la página
st.set_page_config(page_title="Generador Gasolineras", layout="wide")

st.title("⛽ Generador: Gasolineras más baratas de España")
st.markdown("Sube el archivo `.xls` o `.csv` del MITECO. El sistema generará el texto formateado y **tablas en JPG con el diseño corporativo de Noticias Trabajo**.")

if not os.path.exists("logo.png"):
    st.warning("⚠️ No se ha encontrado el archivo 'logo.png' en la misma carpeta que este script. Las imágenes se generarán sin logo.")

def generar_imagen_tabla(df_top, tipo_combustible):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.axis('off')
    
    # --- COLORES CORPORATIVOS FORZADOS ---
    COLOR_CABECERA = '#0A2540'       
    COLOR_TEXTO_CABECERA = '#FFFFFF' 
    COLOR_FILA_PAR = '#F4F6F9'       
    COLOR_FILA_IMPAR = '#FFFFFF'     
    COLOR_PRECIO = '#FF6600'         
    COLOR_BORDES = '#CCCCCC'         
    
    datos = []
    col_precio = 'Precio gasolina 95 E5' if tipo_combustible == 'gasolina' else 'Precio gasóleo A'
    
    for i, (_, row) in enumerate(df_top.iterrows(), 1):
        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
        provincia = str(row['Provincia'])
        ubicacion = f"{localidad} ({provincia})"
        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN RÓTULO"
        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
        precio = f"{row[col_precio]:.3f} €/L"
        
        if len(direccion) > 35: direccion = direccion[:32] + "..."
        if len(rotulo) > 20: rotulo = rotulo[:17] + "..."
        if len(ubicacion) > 28: ubicacion = ubicacion[:25] + "..."
        
        datos.append([f"{i}", ubicacion, rotulo, direccion, precio])
        
    columnas = ["Pos.", "Municipio (Provincia)", "Rótulo", "Dirección", "Precio"]
    
    tabla = ax.table(cellText=datos, colLabels=columnas, loc='center', cellLoc='center')
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(11)
    tabla.scale(1, 2.5) 
    
    for (row, col), cell in tabla.get_celld().items():
        cell.set_edgecolor(COLOR_BORDES)
        
        if row == 0:
            cell.set_facecolor(COLOR_CABECERA)
            cell.set_text_props(weight='bold', color=COLOR_TEXTO_CABECERA, fontsize=12)
        else:
            cell.set_facecolor(COLOR_FILA_PAR if row % 2 == 0 else COLOR_FILA_IMPAR)
            if col == 0:
                cell.set_text_props(weight='bold', color='#555555')
            if col == 4: 
                cell.set_text_props(weight='bold', color=COLOR_PRECIO, fontsize=13) 
                
        if col == 0: cell.set_width(0.06)   
        elif col == 1: cell.set_width(0.26) 
        elif col == 2: cell.set_width(0.20) 
        elif col == 3: cell.set_width(0.33) 
        elif col == 4: cell.set_width(0.15) 
            
    titulo = "Gasolineras más baratas - Gasolina 95" if tipo_combustible == 'gasolina' else "Gasolineras más baratas - Diésel"
    plt.figtext(0.10, 0.88, titulo, fontsize=18, fontweight='bold', color=COLOR_CABECERA, fontfamily='sans-serif')
    
    if os.path.exists("logo.png"):
        try:
            logo = Image.open("logo.png").convert("RGBA")
            ax_logo = fig.add_axes([0.75, 0.84, 0.15, 0.10]) 
            ax_logo.imshow(logo)
            ax_logo.axis('off')
        except Exception as e:
            print(f"Error cargando logo: {e}")

    buf = io.BytesIO()
    plt.savefig(buf, format='jpg', bbox_inches='tight', dpi=300, facecolor='#FFFFFF')
    plt.close(fig)
    buf.seek(0)
    return buf

uploaded_file = st.file_uploader("Arrastra aquí tu archivo XLS o CSV", type=['xls', 'xlsx', 'csv'])

if uploaded_file is not None:
    try:
        content = uploaded_file.read()
        df = None
        
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
                
        if df is None:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, skiprows=3)
            df.columns = df.columns.str.strip()

        if df is None or 'Precio gasolina 95 E5' not in df.columns:
            st.error("❌ No se encontraron las columnas esperadas en el archivo.")
        else:
            with st.spinner("Procesando datos y generando listados e imágenes corporativas..."):
                def limpiar_precio(x):
                    if pd.isna(x) or x == '': return np.nan
                    x = str(x).replace(',', '.')
                    try: return float(x)
                    except: return np.nan

                df['Precio gasolina 95 E5'] = df['Precio gasolina 95 E5'].apply(limpiar_precio)
                df['Precio gasóleo A'] = df['Precio gasóleo A'].apply(limpiar_precio)
                df['Provincia'] = df['Provincia'].astype(str).str.title()
                provincias = sorted([p for p in df['Provincia'].unique() if p.lower() not in ['nan', '']])

                provincias_fuera = ['Ceuta', 'Melilla', 'Balears (Illes)', 'Santa Cruz De Tenerife', 'Palmas (Las)']
                df_peninsula = df[~df['Provincia'].isin(provincias_fuera)]

                top_10_gas = df_peninsula.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(10)
                top_10_die = df_peninsula.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(10)

                img_gasolina = generar_imagen_tabla(top_10_gas, 'gasolina')
                img_diesel = generar_imagen_tabla(top_10_die, 'diesel')
                
                fecha_hoy = datetime.now().strftime("%d-%m-%Y")
                nombre_img_gasolina = f"gasolineras-mas-baratas-gasolina-{fecha_hoy}.jpg"
                nombre_img_diesel = f"gasolineras-mas-baratas-diesel-{fecha_hoy}.jpg"

                html_lines = ["<h2>Top 10: Las gasolineras más baratas de la Península</h2>",
                              "<p>Listado de las 10 estaciones de servicio con los precios más bajos en la España peninsular (excluyendo Baleares, Canarias, Ceuta y Melilla).</p>",
                              "<h3>⛽ Top 10 Gasolina 95 E5 más barata</h3>", "<ul>"]
                
                for _, row in top_10_gas.iterrows():
                    prov, loc = str(row['Provincia']), str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
                    rot, direc = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO", str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                    html_lines.append(f"    <li><strong>{loc} ({prov})</strong>: {rot}, {direc} - <strong>{row['Precio gasolina 95 E5']:.3f} &euro;/L</strong></li>")
                
                html_lines.extend(["</ul>", "<h3>🛢️ Top 10 Diésel (Gasóleo A) más barato</h3>", "<ul>"])
                
                for _, row in top_10_die.iterrows():
                    prov, loc = str(row['Provincia']), str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
                    rot, direc = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO", str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                    html_lines.append(f"    <li><strong>{loc} ({prov})</strong>: {rot}, {direc} - <strong>{row['Precio gasóleo A']:.3f} &euro;/L</strong></li>")
                
                html_lines.extend(["</ul>", "<hr>", "<h2>Las gasolineras más baratas por provincia</h2>", 
                                   "<p>En la web del Ministerio para la Transición Ecológica (MITECO), se puede consultar cuáles son las gasolineras más baratas en cada provincia. El siguiente listado muestra las estaciones con los precios más bajos en toda España.</p>"])

                for prov in provincias:
                    html_lines.extend([f"<h3>{prov}</h3>", "<ul>"])
                    df_prov = df[df['Provincia'] == prov]
                    
                    for _, row in df_prov.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(2).iterrows():
                        loc, rot = str(row['Localidad']).title() if pd.notna(row['Localidad']) else "", str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO"
                        direc = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                        html_lines.append(f"    <li>{loc}, {rot}, {direc}, {row['Precio gasolina 95 E5']:.3f} &euro;/L (Gasolina 95)</li>")
                        
                    for _, row in df_prov.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(2).iterrows():
                        loc, rot = str(row['Localidad']).title() if pd.notna(row['Localidad']) else "", str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN RÓTULO"
                        direc = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
                        html_lines.append(f"    <li>{loc}, {rot}, {direc}, {row['Precio gasóleo A']:.3f} &euro;/L (Diesel A)</li>")
                    html_lines.append("</ul>")

                html_final = "\n".join(html_lines)

            st.success("✅ ¡Listados e imágenes corporativas generadas con éxito!")
            
            st.subheader("🖼️ Descarga las imágenes del Top 10")
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(img_gasolina, width='stretch')
                st.download_button(label="📥 Descargar JPG Gasolina", data=img_gasolina, file_name=nombre_img_gasolina, mime="image/jpeg")
                
            with col2:
                st.image(img_diesel, width='stretch')
                st.download_button(label="📥 Descargar JPG Diésel", data=img_diesel, file_name=nombre_img_diesel, mime="image/jpeg")

            st.markdown("---")
            st.info("👇 **Instrucciones:** Selecciona todo el texto de abajo con el ratón, cópialo y pégalo directamente en la vista visual de tu editor Easywing.")
            st.markdown(html_final, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Ha ocurrido un error inesperado al procesar el archivo: {e}")