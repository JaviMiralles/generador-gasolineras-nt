import pandas as pd
import numpy as np

ruta_archivo = 'preciogaso.xls'

print("Leyendo el archivo Excel...")
try:
    # Usamos read_excel ya que ahora sabemos seguro que es un Excel binario
    df = pd.read_excel(ruta_archivo, skiprows=3)
except Exception as e:
    print(f"Error al leer el archivo Excel: {e}")
    exit()

# LA CLAVE: Limpiar los espacios invisibles en los nombres de las columnas
df.columns = df.columns.str.strip()

# Validar que existe la columna
if 'Precio gasolina 95 E5' not in df.columns:
    print("ERROR: No se encuentra la columna 'Precio gasolina 95 E5'.")
    print("Columnas detectadas en el archivo:", df.columns.tolist())
    exit()

def limpiar_precio(x):
    if pd.isna(x) or x == '': 
        return np.nan
    x = str(x).replace(',', '.')
    try:
        return float(x)
    except:
        return np.nan

df['Precio gasolina 95 E5'] = df['Precio gasolina 95 E5'].apply(limpiar_precio)
df['Precio gasóleo A'] = df['Precio gasóleo A'].apply(limpiar_precio)

df['Provincia'] = df['Provincia'].astype(str).str.title()
provincias = sorted([p for p in df['Provincia'].unique() if p.lower() not in ['nan', '']])

resultado = []
resultado.append("[")
resultado.append("## Las gasolineras más baratas por provincias para echar gasolina o diesel")
resultado.append("En la web del Ministerio para la Transición Ecológica (MITECO), en su sección de “Precio de carburantes en las gasolineras españolas”, se puede consultar cuáles son las gasolineras más baratas en cada provincia española. El siguiente listado muestra las gasolineras con los precios más bajos en todas las provincias de España.")

for prov in provincias:
    resultado.append("")
    resultado.append(f"**{prov}**")
    
    df_prov = df[df['Provincia'] == prov]
    
    # Gasolina
    gas_df = df_prov.dropna(subset=['Precio gasolina 95 E5']).sort_values('Precio gasolina 95 E5').head(2)
    for _, row in gas_df.iterrows():
        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN ROTULO"
        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
        precio = f"{row['Precio gasolina 95 E5']:.3f}"
        resultado.append(f"- {localidad}, {rotulo}, {direccion}, {precio} €/L (Gasolina 95)")
        
    # Diesel
    die_df = df_prov.dropna(subset=['Precio gasóleo A']).sort_values('Precio gasóleo A').head(2)
    for _, row in die_df.iterrows():
        localidad = str(row['Localidad']).title() if pd.notna(row['Localidad']) else ""
        rotulo = str(row['Rótulo']) if pd.notna(row['Rótulo']) else "SIN ROTULO"
        direccion = str(row['Dirección']).title() if pd.notna(row['Dirección']) else ""
        precio = f"{row['Precio gasóleo A']:.3f}"
        resultado.append(f"- {localidad}, {rotulo}, {direccion}, {precio} €/L (Diesel A)")

resultado.append("")
resultado.append("]")

texto_final = "\n".join(resultado)
print(texto_final)