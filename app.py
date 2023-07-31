#%%writefile app.py

import folium
import streamlit as st
from streamlit_folium import st_folium, folium_static
import pandas as pd
import json
from urllib.request import urlopen
from io import BytesIO

#(allow_output_mutation=True)
@st.cache_data 
def carregar_dados():
	print("lendo dados")

	#resp = urlopen("https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json")
	#geo_munic = json.load(BytesIO(resp.read()))
	with open('geo_munic.json', 'r') as openfile:
	    geo_munic = json.load(openfile)
	print("leu geo municipios")

	geo_uf = pd.read_csv("https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/estados.csv")
	print("leu geo uf")

	#df = pd.read_csv("https://raw.githubusercontent.com/gabriellimagomes15/eleicoes/main/grupo.csv")
	df = pd.read_csv("grupo2.csv")
	df.NR_TURNO = df.NR_TURNO.astype(str)

	print("leu geo df")

	return geo_munic, geo_uf, df

@st.cache_resource 
def plot_mapa(dict_query):
	query = monta_query(dict_query)

	#soma = df.query(f"SG_UF == '{filtro_uf}' ").groupby(['NM_MUNICIPIO']).QT_VOTOS_NOMINAIS_VALIDOS.sum().reset_index()
	filtro_df = df.query(f"{query}")


	soma = (filtro_df.groupby(['NM_MUNICIPIO']).QT_VOTOS_NOMINAIS_VALIDOS
			.sum().reset_index().rename(columns = {"QT_VOTOS_NOMINAIS_VALIDOS":"QT_VOTOS"})
			)

	
	soma_munic = soma.set_index('NM_MUNICIPIO')['QT_VOTOS']
	print("LEN:",len(soma_munic),"\n")

	soma_munic = (soma_munic / soma_munic.sum()) * 100
	#soma_munic = soma_munic[:]

	#soma_munic[soma_munic > 8] = soma_munic.median()
	soma['PERCT_VOTOS'] = (soma.QT_VOTOS / soma.QT_VOTOS.sum()) * 100
	soma['PERCT_VOTOS'] = soma['PERCT_VOTOS'].apply(lambda x: f"""{round(x,2)}%""")

	geo_munic_select = {'type': 'FeatureCollection'}
	geo_munic_select['features'] = []
	x = geo_munic['features']
	for muni in x:
		muni['properties']['name'] = muni['properties']['name'].upper()
		if muni['properties']['name'] in soma_munic.index:
		  geo_munic_select['features'].append(muni)

	#colormap = linear.YlOrRd_09.scale(soma_munic.min(),soma_munic.max() )
	#colormap2 = linear.Blues_09.scale(soma_munic.min(),soma_munic.max() )
	filtro_uf = dict_query['SG_UF']
	lat_ = geo_uf.query(f"uf == '{filtro_uf}'").latitude
	long_ = geo_uf.query(f"uf == '{filtro_uf}'").longitude

	print("GERANDO MAPA\n")
	m = folium.Map(
	  #tiles="Cartodb Positron",
	  #tiles="Stamen Watercolor",
	  width="100%", height="100%",
	  #width=900, height=600,
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
	  legend_name="Votos Eleições 2020 (em %)"
	).add_to(m)

	return m,soma,filtro_df


@st.cache_resource
def monta_query(*argumentos):
	query = "and "
	list_query = []
	field_query = argumentos[0] 
	for key in field_query:
		value_query = field_query[key]
		if value_query != "TODOS":
			#print(""" query.join() += f"{k} = '{dict_query[k]}' """)
			if isinstance(value_query,list):
				list_query.append( f" {key} in {value_query} ")
			else:
				list_query.append( f" {key} == '{value_query}' ")

	query = query.join(list_query)
	return query

geo_munic, geo_uf, df = carregar_dados()

#@st.cache_resource(experimental_allow_widgets=True)
#def main():
FILTRO_UF 		= st.sidebar.selectbox('SELECIONE A UF:', df.sort_values('SG_UF').SG_UF.unique() )

FILTRO_NR_TURNO = st.sidebar.selectbox('SELECIONE O TURNO :', 
	df.query(f"SG_UF == '{FILTRO_UF}'").NR_TURNO.unique())

FILTRO_NM_MUNICIPIO = "TODOS" #st.sidebar.selectbox('SELECIONE O MUNICÍPIO :', df.NM_MUNICIPIO.unique() )

FILTRO_DS_CARGO 	= st.sidebar.selectbox('SELECIONE CARGO :', 
	df.query(f"SG_UF == '{FILTRO_UF}' and NR_TURNO == '{FILTRO_NR_TURNO}' ").sort_values('DS_CARGO').DS_CARGO.unique() )

FILTRO_SG_PARTIDO 	= st.sidebar.selectbox('SELECIONE PARTIDO:', 
	(df.query(f"SG_UF == '{FILTRO_UF}' and NR_TURNO == '{FILTRO_NR_TURNO}' and DS_CARGO == '{FILTRO_DS_CARGO}' ")
		.sort_values('SG_PARTIDO').SG_PARTIDO.unique() ) )

FILTRO_DS_SIT_TOT_TURNO = "TODOS" #st.sidebar.selectbox('SELECIONE SITUAÇÃO TURNO :', df.DS_SIT_TOT_TURNO.unique() )

dict_query = {
	  "NR_TURNO": FILTRO_NR_TURNO,
	  "SG_UF": FILTRO_UF,
	  "NM_MUNICIPIO": FILTRO_NM_MUNICIPIO,
	  "DS_CARGO": FILTRO_DS_CARGO,
	  "SG_PARTIDO": FILTRO_SG_PARTIDO,
	  "DS_SIT_TOT_TURNO": FILTRO_DS_SIT_TOT_TURNO          
	}
#	return dict_query


#dict_query = main()
#if st.sidebar.button('Gerar gráfico'):
	
	#monta_query1(p1,p2)
	#st.write('query:', query)

	#filtro_uf = 'RO'

titulos_guias = ['Análise 1 UF', 'Tópico B', 'Tópico C']
guia1, guia2, guia3 = st.tabs(titulos_guias)


with guia1:
	m,soma_df,filtro_uf = plot_mapa(dict_query)

	col1, col2, col3 = st.columns(3)
	col1.metric("QTD Candidatos", filtro_uf.NM_CANDIDATO.nunique()) #, "1.2 °F")
	col2.metric("QTD Eleitos", len(filtro_uf.query("DS_SIT_TOT_TURNO=='ELEITO'").DS_SIT_TOT_TURNO) ) #, "-8%")
	col3.metric("Proporção Votos (total)", f"""
									{round(filtro_uf.QT_VOTOS_NOMINAIS_VALIDOS.sum()/
									df.query(f"SG_UF == '{FILTRO_UF}' and NR_TURNO == '{FILTRO_NR_TURNO}' and DS_CARGO == '{FILTRO_DS_CARGO}' ").QT_VOTOS_NOMINAIS_VALIDOS.sum(),3 )*100} %""" ) #, , "4%")

	with st.container():
		#col1 = st.columns([1])

		#with col1:
			# call to render Folium map in Streamlit
			#st_data = st_folium(m, width=725)
			#st_data = 
		folium_static(m, width=600)
	
	with st.container():
		col2,col3 = st.columns([0.8,0.2])

		with col2:
			st.header('Votos')
			st.dataframe(soma_df.rename(columns = {'NM_MUNICIPIO':'MUNICIPIO',
										 'PERCT_VOTOS':'% Votos'} ),
						width = 500)#.sort_values("QT_VOTOS_NOMINAIS_VALIDOS"))  # Same as st.write(df)

	