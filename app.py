#%%writefile app.py

import folium
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import json
from urllib.request import urlopen
from io import BytesIO

print("lendo dados")

#resp = urlopen("https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json")
#geo_munic = json.load(BytesIO(resp.read()))
with open('geo_munic.json', 'r') as openfile:
    geo_munic = json.load(openfile)
print("leu geo municipios")

geo_uf = pd.read_csv("https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/estados.csv")
print("leu geo uf")

df = pd.read_csv("https://raw.githubusercontent.com/gabriellimagomes15/eleicoes/main/grupo.csv")
print("leu geo df")


def plot_mapa():
  soma = df.query(f"SG_UF == '{filtro_uf}' ").groupby(['NM_MUNICIPIO']).QT_VOTOS_NOMINAIS_VALIDOS.sum().reset_index()
  soma_munic = soma.set_index('NM_MUNICIPIO')['QT_VOTOS_NOMINAIS_VALIDOS']
  print(len(soma_munic))
  soma_munic = (soma_munic / soma_munic.sum()) * 100
  soma_munic = soma_munic[:]

  soma_munic[soma_munic > 8] = soma_munic.median()

  geo_munic_select = {'type': 'FeatureCollection'}
  geo_munic_select['features'] = []
  x = geo_munic['features']
  for muni in x:
    muni['properties']['name'] = muni['properties']['name'].upper()
    if muni['properties']['name'] in soma_munic.index:
      geo_munic_select['features'].append(muni)

  len(geo_munic_select['features'])

  #colormap = linear.YlOrRd_09.scale(soma_munic.min(),soma_munic.max() )
  #colormap2 = linear.Blues_09.scale(soma_munic.min(),soma_munic.max() )

  lat_ = geo_uf.query(f"uf == '{filtro_uf}'").latitude
  long_ = geo_uf.query(f"uf == '{filtro_uf}'").longitude

  m = folium.Map(
      #tiles="Cartodb Positron",
      #tiles="Stamen Watercolor",
      #width="100%", height="100%",
      width=900, height=600,
      location= [lat_,long_],#[-15.77972, -47.92972],
      zoom_start=5
  )

  folium.Choropleth(
      geo_data=geo_munic_select,
      name="choropleth",
      data=soma_munic,
      #data=state_data,
      #columns=["NM_MUNICIPIO", "QT_VOTOS_NOMINAIS_VALIDOS"],
      key_on="properties.name",
      fill_color= "OrRd",#"YlOrRd", #"YlGn",
      #fill_opacity=0.7,
      #line_opacity=0.2,
      legend_name="Votos Eleições 2020"
  ).add_to(m)
  return m


st.title('Eleições de')

filtro_uf = st.selectbox('SELECIONE A UF:', 
	df.SG_UF.unique() )

st.write('UF SELECIONADA:', filtro_uf)

#filtro_uf = 'RO'
m = plot_mapa()

# call to render Folium map in Streamlit
st_data = st_folium(m, width=725)
