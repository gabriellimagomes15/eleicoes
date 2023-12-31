#%%writefile app.py

import folium
import streamlit as st
from streamlit_folium import st_folium, folium_static
import pandas as pd
import json
from urllib.request import urlopen
from io import BytesIO
import numpy as np
import plotly.express as px
from branca.colormap import linear

@st.cache_data 
def retorna_geo_munic(lista_munic):
  geo_munic_selecionado = {'type': 'FeatureCollection'}
  geo_munic_selecionado['features'] = []

  for muni in geo_munic['features'][:]:
        #print(muni)
        if muni['properties']['name'].upper() in lista_munic:
            geo_munic_selecionado['features'].append(muni)
  return geo_munic_selecionado

@st.cache_data 
def carregar_dados():
	print("lendo dados")

	#resp = urlopen("https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json")
	#geo_munic = json.load(BytesIO(resp.read()))
	with open('geo_munic.json', 'r') as openfile:
	    geo_munic = json.load(openfile)
	print("leu geo municipios")

	#geo_uf = pd.read_csv("https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/estados.csv")
	#print("leu geo uf")

	#df = pd.read_csv("https://raw.githubusercontent.com/gabriellimagomes15/eleicoes/main/grupo.csv")
	df = pd.read_csv("grupo2.csv")
	df.NR_TURNO = df.NR_TURNO.astype(str)

	print("leu df")

	planilha = pd.read_csv("planilha.csv")
	planilha.NR_TURNO = planilha.NR_TURNO.astype(str)

	print("leu planilha")
	
	url = "https://raw.githubusercontent.com/datalivre/Conjunto-de-Dados/master/br_states.json"
	json_url = urlopen(url)
	geo_uf = json.loads(json_url.read())
	print("leu geo uf")
	
	df_qtd_bu = pd.read_csv("df_qtd_bu.csv")
	df_receitas = pd.read_csv("df_receitas.csv")
	df_desp_contrat_paga = pd.read_csv("df_desp_contrat_paga.csv")


	return geo_munic, geo_uf, df, planilha,df_qtd_bu,df_receitas,df_desp_contrat_paga

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

@st.cache_data 
def monta_planilha(dados):
	#QTD VOTOS GERAL
	qtd_geral = dados.groupby(["SG_UF","NM_MUNICIPIO","SG_PARTIDO"]).agg({"QT_VOTOS_NOMINAIS_VALIDOS":'sum'}).reset_index()

	# QTD VOTOS POR CARGO
	qtd_cargo = dados.groupby(["SG_UF","NM_MUNICIPIO","SG_PARTIDO","DS_CARGO"]).agg({"QT_VOTOS_NOMINAIS_VALIDOS":'sum'}).reset_index()
	qtd_cargo = pd.pivot_table(qtd_cargo,index=['SG_UF','NM_MUNICIPIO','SG_PARTIDO'],values='QT_VOTOS_NOMINAIS_VALIDOS',columns = 'DS_CARGO' ).reset_index() #index=['SG_UF','NM_MUNICIPIO','SG_PARTIDO']).reset_index()

	df_qtd_votos = qtd_geral.merge(qtd_cargo, on=["SG_UF","NM_MUNICIPIO","SG_PARTIDO"])

	## CRIANDO NOVAS COLUNAS
	novas_colunas = ["ARRECADAÇAO_TRIBUTARIA","ORÇAMENTO_MUNICIPAL","VICE-PREFEITURA","DEPT_ESTADUAL_2022","DEPT_FEDERAL_202","SENADO_2022","GOVERNO_DE_ESTADO","DISPERSAO_DO_1_TURNO_2022",
	"BAN","DIRETÓRIO_MAIS_DE_1_ANO","FUNDO_ELEITORAL_2020","DOAÇÕES_2020","FUNDO_PARTIDARIO_2020","TOTAL_DE_RECEITAS","TOTAL_DE_DESPESAS",
	"TOTAL_DE_DESPESAS_PAGAS","TOTAL_DE_PENDENCIAS"]

	for col in novas_colunas:
	  df_qtd_votos[col] = "PENDENTE"
	  
	df_qtd_votos.columns = [c.upper() for c in df_qtd_votos.columns]

	return df_qtd_votos

@st.cache_data 
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(sep=';', index = False ).encode('latin1')


titulos_guias = ['Planilha','Análise','text']
guia1, guia2, guia3 = st.tabs(titulos_guias)


## CARREGANDO DADOS
geo_munic, geo_uf, df, planilha, df_qtd_bu, df_receitas,df_desp_contrat_paga = carregar_dados()

with guia1:
	#with st.container():
	col1,col2 = st.columns([0.9,0.1])

	with col1:

		#monta_query(dict_query)
		#print(planilha.columns)
		df_planilha = planilha.copy() #monta_planilha(df)
		df_planilha.ANO_ELEICAO = df_planilha.ANO_ELEICAO.astype("str") 
		
		st.title(f'Planilha Geral ' )
		st.markdown(f"""Visualização das 20 primeiras linhas. """)
		st.markdown(f"""Para visualizar todas as **{len(df_planilha)}** linhas fazer download do arquivo.""")
		st.dataframe( df_planilha.head(20), width = 750)

		csv = convert_df(df_planilha)
		st.download_button( label="Download Dados(.csv)",data=csv,
							file_name='eleicoes.csv', mime='text/csv')
		
		

		st.title(f'Planilha Boletim de Urna (ZONA ELEITORA) ' )

		df_bu = df_qtd_bu.copy() #monta_planilha(df)
		df_bu.ANO_ELEICAO = df_bu.ANO_ELEICAO.astype("str") 
		
		st.markdown(f"""Visualização das 20 primeiras linhas. """)
		st.markdown(f"""Para visualizar todas as **{len(df_bu)}** linhas fazer download do arquivo.""")
		st.dataframe( df_bu.head(20), width = 750)

		csv_bu = convert_df(df_bu)
		st.download_button( label="Download Dados(.csv)",data=csv_bu,
							file_name='boletim_urna.csv', mime='text/csv')

		st.title(f'Planilha RECEITAS' )

		df_receitas2 = df_receitas.copy() #monta_planilha(df)
		df_receitas2.ANO_ELEICAO = df_receitas2.ANO_ELEICAO.astype("str") 
		
		st.markdown(f"""Visualização das 20 primeiras linhas. """)
		st.markdown(f"""Para visualizar todas as **{len(df_receitas2)}** linhas fazer download do arquivo.""")
		st.dataframe( df_receitas2.head(20), width = 750)

		csv_receitas = convert_df(df_receitas2)
		st.download_button( label="Download Dados(.csv)",data=csv_receitas,
							file_name='receitas.csv', mime='text/csv')

		st.title(f'Planilha DESPESAS' )

		df_despespas2 = df_desp_contrat_paga.copy() #monta_planilha(df)
		df_despespas2.ANO_ELEICAO = df_despespas2.ANO_ELEICAO.astype("str") 
		
		st.markdown(f"""Visualização das 20 primeiras linhas. """)
		st.markdown(f"""Para visualizar todas as **{len(df_despespas2)}** linhas fazer download do arquivo.""")
		st.dataframe( df_despespas2.head(20), width = 750)

		csv_despesas = convert_df(df_despespas2)
		st.download_button( label="Download Dados(.csv)",data=csv_despesas,
							file_name='despesas.csv', mime='text/csv')

with guia2:
	FILTRO_SG_PARTIDO = st.selectbox('Selecione o partido:', df_qtd_bu.sort_values('SG_PARTIDO').SG_PARTIDO.unique())
	
	FILTRO_DS_CARGO = st.selectbox('Selecione o partido:', df_qtd_bu.DS_CARGO_PERGUNTA.unique())

	#FILTRO_NR_TURNO = st.radio('Selecione o turno:', df_qtd_bu.NR_TURNO.unique())
	if "load_map" not in st.session_state:
		st.session_state.load_map = False

	botao_filtrar = st.button('Filtrar')

	if botao_filtrar:
		st.session_state.load_map = True

		dict_query = {
			  #"NR_TURNO": FILTRO_NR_TURNO,
			  "DS_CARGO_PERGUNTA": FILTRO_DS_CARGO,
			  "SG_PARTIDO": FILTRO_SG_PARTIDO          
			}

		query = monta_query(dict_query)
		df_eleitos = df_qtd_bu.query(' and '.join( [query, "DS_SIT_TOT_TURNO == 'ELEITO'" ]))
		df_nao_eleitos = df_qtd_bu.query(' and '.join( [query, "DS_SIT_TOT_TURNO != 'ELEITO'" ]))

		qtd_total = len(df_eleitos) + len(df_nao_eleitos)
		qtd_eleitos = len(df_eleitos)
		qtd_nao_eleitos = len(df_nao_eleitos)

		st.markdown(f"""QTD CANDIDATOS: **{qtd_total}** """)
		st.markdown(f"""QTD ELEITOS: **{qtd_eleitos}({np.round((qtd_eleitos/qtd_total)*100)}%)**""")
		st.markdown(f"""QTD NÃO ELEITOS: **{qtd_nao_eleitos}({np.round((qtd_nao_eleitos/qtd_total)*100)}%)**""")
		
		geo_munic_eleitos     = retorna_geo_munic(df_eleitos.NM_MUNICIPIO.unique())
		geo_munic_nao_eleitos = retorna_geo_munic(df_nao_eleitos.NM_MUNICIPIO.unique())

		dict_query_despesas = {"SG_PARTIDO": FILTRO_SG_PARTIDO}
		df_despesas_partido = df_desp_contrat_paga.query(monta_query(dict_query_despesas))

		soma_despesas = (df_despesas_partido.groupby(['ANO_ELEICAO','NR_TURNO',
		                                             'SG_UF'])
		                  .agg(TOTAL_DESPESAS = ('VR_PAGTO_DESPESA', 'sum'))
		                  .reset_index()
		                )

		df_total_despesas = (soma_despesas.groupby(['ANO_ELEICAO','SG_UF'])
		                  .agg(TOTAL_DESPESAS = ('TOTAL_DESPESAS', 'sum'))
		                  .reset_index())

		dados2 = df_total_despesas.set_index('SG_UF')['TOTAL_DESPESAS']
		dados2_log = np.log(dados2)

		dados_cores = dados2_log.copy()
		cores = linear.OrRd_09.scale(dados_cores.min(),dados_cores.max(),max_labels = 3)


		#if botao_filtrar and st.session_state.load_map:
		#st.session_state.load_map = False

		m = folium.Map(
				  width="100%", height="100%",
				  location= [-15.77972, -47.92972],
				  zoom_start=4
				)
		cores.caption = "Despesas"
		cores.add_to(m)

		folium.GeoJson(geo_uf,
           style_function = lambda x:{
               "fillColor": cores(dados_cores[x['id']]) if x['id'] in dados2.index else 'black',
               "weight":0.3,
           }).add_to(m)


		r2 = [ x['geometry']['coordinates'][0][0] for x in geo_munic_nao_eleitos['features'] ]#.keys()
		radius = 3
		for x in r2:
		  folium.CircleMarker(
				location =  [x[1],x[0]], #[lat_, long_],
				radius = radius,
				color  = "red",# "cornflowerblue",
				stroke = False,
				weight = 0.5,
				fill   = True,
				fill_opacity = 0.6,
				opacity = 1,
				#popup   = "{} pixels".format(radius),
				#tooltip = "I am in pixels",
		    ).add_to(m)

		r2 = [ x['geometry']['coordinates'][0][0] for x in geo_munic_eleitos['features'] ]#.keys()
		radius = 3.5
		for x in r2:
		  folium.CircleMarker(
		      	location =  [x[1],x[0]], #[lat_, long_],
				radius = radius,
				color  = "green",# "cornflowerblue",
				stroke = False,
				weight = 0.5,
				fill   = True,
				fill_opacity = 0.8,
				opacity = 1,
				#popup   = "{} pixels".format(radius),
				#tooltip = "I am in pixels",
		    ).add_to(m)

		folium_static(m)