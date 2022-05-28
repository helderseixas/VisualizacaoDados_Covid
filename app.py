# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import os
import plotly.express as px
from dash import dcc
from dash import html
import pandas as pd
import geopandas as gpd
import geobr

#--------------- Carrega dados ---------
# Dados da Covid-19
diretorio_covid = os.fsencode('dados/covid')
df_covid_base = None
for arquivo in os.listdir(diretorio_covid):
    nome_arquivo = 'dados/covid/' + os.fsdecode(arquivo)
    df_temp = pd.read_csv(nome_arquivo, decimal=',', sep=';')
    if df_covid_base is None:
        df_covid_base = df_temp
    else:
        df_covid_base = pd.concat([df_covid_base, df_temp])

df_covid_base.data = pd.to_datetime(df_covid_base.data, infer_datetime_format=True)
df_covid_base = df_covid_base.sort_values('data')

df_municipios = df_covid_base[df_covid_base.municipio.isnull() == False].copy()
df_municipios['codmun']  = df_municipios.codmun.astype('Int64').astype(str)
df_brasil = df_municipios.groupby(['data', 'semanaEpi']).sum()[['populacaoTCU2019', 'casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos']].reset_index()
df_regioes = df_municipios.groupby(['regiao', 'data', 'semanaEpi']).sum()[['populacaoTCU2019', 'casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos']].reset_index()

fim_primeira_onda = '2020-11-10'
fim_segunda_onda = '2022-01-02'

#Dados geográficos
try:
    nome_arquivo = "dados/mapa_municipios.geojson"
    mapa_municipios = gpd.read_file(nome_arquivo, driver='GeoJSON')
except:
    mapa_municipios = geobr.read_municipality(year=2020)
    mapa_municipios['code_muni']  = mapa_municipios.code_muni.astype('Int64').astype(str)
    mapa_municipios['code_muni_6'] = mapa_municipios.code_muni.apply(lambda code_muni: code_muni[:6])
    mapa_municipios.to_file("dados/mapa_municipios.geojson", driver='GeoJSON')


#----------------Cria gráficos ----------------
# Série de óbitos no Brasil
df_brasil['obitosNovosMedia14Dias'] = df_brasil[['obitosNovos']].rolling(window=14).mean()

figura_obitos_brasil = px.line(df_brasil, x='data', y='obitosNovosMedia14Dias', color=px.Constant('Média móvel de 14 dias'))
figura_obitos_brasil.add_bar(x=df_brasil.data, y=df_brasil.obitosNovos, name='Novos óbitos')
figura_obitos_brasil.add_vline(x=fim_primeira_onda, line_dash="dash")
figura_obitos_brasil.add_annotation(x=fim_primeira_onda, y=1, yref="paper", text="Fim da primeira onda")
figura_obitos_brasil.add_vline(x=fim_segunda_onda, line_dash="dash")
figura_obitos_brasil.add_annotation(x=fim_segunda_onda, y=1, yref="paper", text="Fim da segunda onda")

#Série acumulada de óbitos por região
df_regioes['taxaObitosAcumulado'] = df_regioes.obitosAcumulado / df_regioes.populacaoTCU2019 * 100000

figura_obitos_regioes = px.line(df_regioes, x='data', y='taxaObitosAcumulado', color='regiao')
figura_obitos_regioes.add_vline(x=fim_primeira_onda, line_dash="dash")
figura_obitos_regioes.add_annotation(x=fim_primeira_onda, y=1, yref="paper", text="Fim da primeira onda")
figura_obitos_regioes.add_vline(x=fim_segunda_onda, line_dash="dash")
figura_obitos_regioes.add_annotation(x=fim_segunda_onda, y=1, yref="paper", text="Fim da segunda onda")

#Mapa da taxa de mortalidade
# geodf_municipios = df_municipios[df_municipios.data == df_municipios.data.max()].merge(mapa_municipios, left_on='codmun', right_on='code_muni_6').set_index('municipio')
# geodf_municipios['Taxa de mortalidade'] = geodf_municipios.obitosAcumulado / geodf_municipios.populacaoTCU2019 * 100000
# figura_mapa_mortalidade = px.choropleth(geodf_municipios,
#                                         geojson=geodf_municipios.geometry,
#                                         locations=geodf_municipios.index,
#                                         color="code_state")
# figura_mapa_mortalidade.update_geos(fitbounds="locations", visible=False)



#----------------Exibir painel Covid-BR ------------------


app = Dash(__name__)

app.layout = html.Div([
    html.H1("Painel Covid-BR"),
    html.Div(children=[
        dcc.Graph(id='figura_obitos_brasil', figure=figura_obitos_brasil, style={'display': 'inline-block'}),
        dcc.Graph(id='figura_obitos_regioes', figure=figura_obitos_regioes, style={'display': 'inline-block'})
    ]),
    html.Div(dcc.Graph(figure=figura_mapa_mortalidade))
])

if __name__ == '__main__':
    app.run_server(debug=True)