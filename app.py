import streamlit as st
import pandas as pd
import numpy as np
import io

# Configuración básica de la página
st.set_page_config(page_title="Generador Gasolineras", layout="wide")

st.title("⛽ Generador: Gasolineras más baratas de España")
st.markdown("Sube el archivo `.xls` o `.csv` descargado del MITECO. El sistema procesará los datos y te mostrará el texto formateado para que solo tengas que **seleccionarlo con el ratón, copiarlo y pegarlo** directamente en la vista visual de tu editor.")

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

                # --- GENERACIÓN DE LA ESTRUCTURA ---
                html_lines = []
                html_lines.append("<h2>Las gasolineras más baratas por provincias para echar gasolina o diesel</h2>")
                html_lines.append("<p>En la web del Ministerio para la Transición Ecológica (MITECO), en su sección de “Precio de carburantes en las gasolineras españolas”, se puede consultar cuáles son las gasolineras más baratas en cada provincia española. El siguiente listado muestra las gasolineras con los precios más bajos en todas las provincias de España.</p>")

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

            st.success("✅ ¡Listado generado con éxito!")
            
            st.info("👇 **Instrucciones:** Selecciona todo el texto que aparece debajo del recuadro con el ratón (desde el título hasta la última provincia), cópialo (**Ctrl+C** o **Cmd+C**) y pégalo directamente en la vista visual de tu editor Easywing. El formato de listas y títulos se mantendrá intacto.")
            
            # Mostramos el resultado renderizado de forma visual y limpia
            st.markdown("---")
            st.markdown(html_final, unsafe_allow_html=True)
            st.markdown("---")
            
    except Exception as e:
        st.error(f"Ha ocurrido un error inesperado al procesar el archivo: {e}")