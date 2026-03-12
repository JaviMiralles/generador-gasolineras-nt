import streamlit as st
import pandas as pd
import numpy as np
import io

# Configuración básica de la página
st.set_page_config(page_title="Generador Gasolineras", layout="wide")

st.title("⛽ Generador: Gasolineras más baratas de España")
st.markdown("Sube el archivo `.xls` o `.csv` descargado del MITECO. El sistema generará un Top nacional (Península) y el listado provincial para que lo copies visualmente a tu editor.")

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
                if len(lineas) > 3:
                    cabecera = lineas[3]
                    separador = ';' if ';' in cabecera else ','
                else:
                    separador = ','
                
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

        # Validación final
        if df is None or 'Precio gasolina 95 E5' not in df.columns:
            st.error("❌ No se encontraron las columnas esperadas en el archivo.")
        else:
            with st.spinner("Procesando datos y generando vista visual..."):
                
                def limpiar_precio(x):
                    if pd.isna(x) or x == '': 
                        return np.nan
                    x = str(x).replace(',', '.')
                    try:
                        return float(x)
                    except:
                        return np.nan

                # Limpieza
                df['Precio gasolina 95 E5'] = df['Precio gasolina 95 E5'].apply(limpiar_precio)
                df['Precio gasóleo A'] = df['Precio gasóleo A'].apply(limpiar_precio)

                df['Provincia'] = df['Provincia'].astype(str).str.title()
                provincias = sorted([p for p in df['Provincia'].unique() if p.lower() not in ['nan', '']])

                html_lines = []

                # -----------------------------------------------------------------
                # 1. TOP PENÍNSULA (Excluyendo islas y ciudades autónomas)
                # -----------------------------------------------------------------
                provincias_fuera = ['Ceuta', 'Melilla', 'Balears (Illes)', 'Santa Cruz De Tenerife', 'Palmas (Las)']
                df_peninsula = df[~df['Provincia'].isin(provincias_fuera)]

                html_lines.append("<h2>Top 5: Las gasolineras más baratas de la Península</h2>")
                html_lines.append("<p>Listado de las estaciones de servicio con los precios más bajos en la España peninsular (excluyendo Baleares, Canarias, Ceuta y Melilla).</p>")

                # Top 5 Gasolina Península
                html_lines.append("<h3>⛽ Top 5 Gasolina 95 E5 más barata</h3>")
                html_lines.append("<ul>")
                top_gas = df_peninsula.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(5)
                for _, row in top_gas.iterrows():
                    provincia = str(row['Provincia'])
                    localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) and row['Localidad'] != '' else ""
                    rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN ROTULO"
                    direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) and row['Dirección'] != '' else ""
                    precio = f"{row['Precio gasolina 95 E5']:.3f}"
                    html_lines.append(f"    <li><strong>{localidad} ({provincia})</strong>: {rotulo}, {direccion} - <strong>{precio} &euro;/L</strong></li>")
                html_lines.append("</ul>")

                # Top 5 Diésel Península
                html_lines.append("<h3>🛢️ Top 5 Diésel (Gasóleo A) más barato</h3>")
                html_lines.append("<ul>")
                top_die = df_peninsula.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(5)
                for _, row in top_die.iterrows():
                    provincia = str(row['Provincia'])
                    localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) and row['Localidad'] != '' else ""
                    rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN ROTULO"
                    direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) and row['Dirección'] != '' else ""
                    precio = f"{row['Precio gasóleo A']:.3f}"
                    html_lines.append(f"    <li><strong>{localidad} ({provincia})</strong>: {rotulo}, {direccion} - <strong>{precio} &euro;/L</strong></li>")
                html_lines.append("</ul>")
                
                html_lines.append("<hr>") # Una línea separadora visual

                # -----------------------------------------------------------------
                # 2. LISTADO POR PROVINCIAS (Todas)
                # -----------------------------------------------------------------
                html_lines.append("<h2>Las gasolineras más baratas por provincia</h2>")
                html_lines.append("<p>En la web del Ministerio para la Transición Ecológica (MITECO), se puede consultar cuáles son las gasolineras más baratas en cada provincia. El siguiente listado muestra las estaciones con los precios más bajos en toda España.</p>")

                for prov in provincias:
                    html_lines.append(f"<h3>{prov}</h3>")
                    html_lines.append("<ul>")
                    
                    df_prov = df[df['Provincia'] == prov]
                    
                    # Gasolina
                    gas_df = df_prov.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(2)
                    for _, row in gas_df.iterrows():
                        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) and row['Localidad'] != '' else ""
                        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN ROTULO"
                        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) and row['Dirección'] != '' else ""
                        precio = f"{row['Precio gasolina 95 E5']:.3f}"
                        html_lines.append(f"    <li>{localidad}, {rotulo}, {direccion}, {precio} &euro;/L (Gasolina 95)</li>")
                        
                    # Diesel
                    die_df = df_prov.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(2)
                    for _, row in die_df.iterrows():
                        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) and row['Localidad'] != '' else ""
                        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) and row['Rótulo'] != '' else "SIN ROTULO"
                        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) and row['Dirección'] != '' else ""
                        precio = f"{row['Precio gasóleo A']:.3f}"
                        html_lines.append(f"    <li>{localidad}, {rotulo}, {direccion}, {precio} &euro;/L (Diesel A)</li>")

                    html_lines.append("</ul>")

                # Unimos todo en un solo bloque
                html_final = "\n".join(html_lines)

            st.success("✅ ¡Listados generados con éxito!")
            
            st.info("👇 **Instrucciones:** Selecciona todo el texto que aparece debajo de la línea con el ratón, cópialo (**Ctrl+C** o **Cmd+C**) y pégalo directamente en tu editor Easywing.")
            
            # Mostramos el resultado
            st.markdown("---")
            st.markdown(html_final, unsafe_allow_html=True)
            st.markdown("---")
            
    except Exception as e:
        st.error(f"Ha ocurrido un error inesperado al procesar el archivo: {e}")