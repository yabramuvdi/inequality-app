import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import flask
from dash.dependencies import Input, Output, State
from scipy.stats import gaussian_kde
from functions import *
import quantecon as qe
import time
from dash.exceptions import PreventUpdate
import random

# Tutorial: https://dash.plotly.com/layout

################################
# 0. colors
################################

grey = '#f7f4eb'
teal = '#3C7A89'
purple = '#37123C'
rose = '#945D5E'
naranja = '#edb183'
naranja_fill = '#ffdcc2'
black = '#001514'

################################
# 1. Data and initial Graphs
################################

df = pd.read_csv('GEIH_mini.csv')
ingreso_original = df.ING_pc_bl_def_arriendo
df.rename(columns={'seccion_2d': 'sector'}, inplace=True)
print(df.shape)

# KDE
start = time.time()
kernel_original = gaussian_kde(ingreso_original,
                               weights=df.fac_exp_ind_12m)
# generate equally spaced X values
xs = np.linspace(0, max(df.ING_pc_bl_def_arriendo), 1000)
dist_original = kernel_original(xs)
print('Kernel calculated in {} minutes'.format((time.time()-start)/60))

fig_hist = go.Figure(
    layout=go.Layout(
        title=go.layout.Title(text=u"Distribución del ingreso, pobreza y "
                                   u"vulnerabilidad"),
        xaxis=go.layout.XAxis(title=u"Ingreso Per Cápita",
                              range=[0, 1000000]),
        yaxis=go.layout.YAxis(visible=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='grey'
    )
)

# Original distribution
fig_hist.add_trace(go.Scatter(x=xs, y=dist_original,
                         mode='lines',
                         name=u'Distribución Original',
                         line=dict(color=black)))

# summary statistics
median_original = weighted_median(df,
                                  'ING_pc_bl_def_arriendo',
                                  'fac_exp_ind_12m')

# Lorenz curve and GINI (https://python.quantecon.org/wealth_dynamics.html)
# TODO: weighted version of these calculations

# start = time.time()
# gini_original = qe.gini_coefficient(df.ING_pc_bl_def_arriendo.to_numpy())
# print('Gini calculated in {} minutes'.format((time.time()-start)/60))

f_vals, l_vals = qe.lorenz_curve(df.ING_pc_bl_def_arriendo.to_numpy())

fig_lorenz = go.Figure(
    layout=go.Layout(
        title=go.layout.Title(text=u"Curva de Lorenz"),
        xaxis=go.layout.XAxis(title="Porcentaje acumulado de personas"),
        yaxis=go.layout.YAxis(title="Porcentaje acumulado del ingreso"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='grey',
        showlegend=True
    )
)

# sample to plot
ids = list(range(0,len(f_vals)))
sample_ids = random.sample(ids,10000)

fig_lorenz.add_trace(go.Scatter(x=[0,1], y=[0,1],
                         mode='lines',
                         name=u'Igualdad total',
                         line=dict(color='grey', dash="dashdot"),
                                fill=None))

fig_lorenz.add_trace(go.Scatter(x=f_vals[sample_ids],
                                y=l_vals[sample_ids],
                         mode='lines',
                         name=u'Distribución Original',
                         line_color=black, fill=None))


# Pobreza 
pobreza_original = calculo_pobreza(df, 'ING_pc_bl_def_arriendo')

################################
# 2. App Layout
################################

app = dash.Dash(__name__)
server = app.server

app.config['suppress_callback_exceptions'] = True
app.layout = html.Div(children=[

    html.Header(
        html.H1(children='Efectos en pobreza y desigualdad '
                                          'del Covid-19'),
        style={'color':'#945D5E'}
    ),

    html.P(
        children= u"Esta aplicación visualiza de forma interactiva los "
                  u"efectos en la distribucuión del ingreso de posibles "
                  u"choques a algunos sectores productivos."),
    html.Hr(),

    #-------------------------
    # user input
    #-------------------------

    html.Div(
        className='three columns',
        children=[
            # ----------------------------
            # 1. Vulnerabilidad Sectorial
            # ----------------------------
            html.H5('Sectores', style={'color': teal}),
            html.P(u'Seleccione los sectores que se verán afectados por el '
                    u'choque', style={'color': 'grey'}),
            dcc.Dropdown(
                id='sectores',
                options=[
                    {'label': 'Actividades Agropecuarias', 'value': 1},
                    {'label': 'Pesca', 'value': 2},
                    {'label': 'Minería', 'value': 3},
                    {'label': 'Manufactura', 'value': 4},
                    {'label': 'Energía', 'value': 5},
                    {'label': 'Construcción', 'value': 6},
                    {'label': 'Comercio y talleres automotores', 'value': 7},
                    {'label': 'Hotelería y restaurantes', 'value': 8},
                    {'label': 'Transporte y comunicaciones', 'value': 9},
                    {'label': 'Finanzas', 'value': 10},
                    {'label': 'Inmobiliaria', 'value': 11},
                    {'label': 'Sector Público', 'value': 12},
                    {'label': 'Educación', 'value': 13},
                    {'label': 'Salud y servicios sociales', 'value': 14},
                    {'label': 'Servicios comunitarios y personales', 'value':
                        15},
                    {'label': 'Servicios a Hogares', 'value': 16},
                    {'label': 'Otras Organizaciones', 'value': 17}
                ],
                multi=True,
                value=None,
                style={"margin-bottom": "3em"}
            ),
            # ----------------------------
            # 2. Vulnerabilidad Trabajadores
            # ----------------------------
            html.H5(u'Características del empleo', style={'color': teal}),
            html.P(u'Tamaño de la empresa', style={'color': 'grey'}),
            html.Div(
                children=[
                    dcc.Dropdown(
                        id='empresa',
                        options=[
                            {'label': 'Pequeña', 'value': 1},
                            {'label': 'Mediana', 'value': 2},
                            {'label': 'Grande', 'value': 3},
                            {'label': 'Gigante', 'value': 4}
                        ], style={"margin-bottom": "1.5em"}),
                    html.P(u'Relación laboral', style={'color': 'grey'}),
                    dcc.Checklist(
                        id='formalidad',
                        options=[
                            {'label': 'Informal', 'value': 1}
                        ]),
                    dcc.Checklist(
                        id='contrato',
                        options=[
                            {'label': u'Contratos Frágiles', 'value': 1},
                        ])
                ], style={'columnCount': 1, "margin-bottom": "3em"}),
            # ----------------------------
            # 3. Magnitud choque
            # ----------------------------
            html.H5(u'Magnitud del choque', style={'color': teal}),
            html.Div([
                dcc.Slider(
                    id='shock',
                    min=0,
                    max=100,
                    marks={i: '{}%'.format(i) for i in range(0,101,20)},
                    value=0,
                )
            ], style={'marginBottom': '3em'}),

            # ----------------------------
            # 4. Actualizar resultados
            # ----------------------------
            html.Button(id='apply-button', n_clicks=0, children='Aplicar',
                        style={'background-color': rose,
                               'color': 'white'})
        ]),

    # -------------------------
    # Tabs
    # -------------------------
    # html.Div(
    #     className= 'eight columns',
    #     children=[
    #         dcc.Tabs(id='tabs', value='tab-1', children=[
    #             dcc.Tab(label=u'Distribución', value='tab-1'),
    #             dcc.Tab(label='Lorenz', value='tab-2'),
    #             dcc.Tab(label='Pobreza', value='tab-3')
    #         ]),
    #         html.Div(id='tabs-content')
    # ]),

    html.Div(className='eight columns',
             children=[
                 dcc.Tabs([
                     dcc.Tab(label=u'Distribución',
                             children=[
                                 dcc.Checklist(id='reference-lines',
                                               options=[
                    {'label': u'Salario Mínimo -',
                     'value': 'Minimum Wage'},
                    {'label': u'Línea de Pobreza -',
                     'value': 'Poverty Line'},
                    {'label': u'Línea de Vulnerabilidad -',
                     'value': 'Vulnerability Line'}
                ],
                                               labelStyle={'display': 'inline-block'},
                                               style={'background-color': 'white',
                                                      'margin-top': '2.5em'}),
                                 dcc.Graph(id='histogram'),
                                 html.P('Mediana distribución original: {:,.0f} COP'.format(median_original)),
                                 html.Div(id='mediana-choque')
                             ]),
                     dcc.Tab(label='Desigualdad',
                             children=[
                                 dcc.Graph(id='lorenz')
                             ]),
                     dcc.Tab(label='Pobreza',
                             children=[
                                 html.H4('Pobreza'),
                                 html.P(
                                     u'Índice de pobreza original: {:.2f}%'.format(pobreza_original)),
                                 html.Div(id='pobreza-choque')
                             ])
                 ])
             ])

    # -------------------------
    # Hidden div inside the app that stores the intermediate value
    # -------------------------
    # html.Div(id='data-shock', style={'display': 'none'})
])


################################
# 3. App Callbacks
################################

# ----------------------------
# Data and Figures update callback
# ----------------------------

@app.callback([Output('histogram', 'figure'),
               Output('mediana-choque', component_property='children'),
               Output('lorenz', 'figure'),
               Output('pobreza-choque', component_property='children')],
              [Input('apply-button', 'n_clicks'),
               Input('reference-lines', 'value')],
              state=[State('sectores', 'value'),
               State('shock', 'value'),
               State('empresa', 'value'),
               State('formalidad', 'value'),
               State('contrato', 'value')])
def update_tabs(n_clicks,
                reference_lines,
                selected_sectors,
                shock,
                empresa,
                formalidad,
                contrato):

    # descriptive statistics
    mediana_choque = 'No choque'
    texto_mediana = 'Mediana choque: {}'.format(mediana_choque)
    pobreza_choque = 'No choque'
    texto_pobreza = u'Índice de pobreza choque: {}'.format(pobreza_choque)

    # get context
    ctx = dash.callback_context
    if not ctx.triggered:
        return fig_hist, texto_mediana, fig_lorenz, texto_pobreza
    else:
        action_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if action_id == 'apply-button':
        # ----------------------------
        # 1. Datos
        print('Updating data...')
        # ----------------------------

        if formalidad is None:
            formalidad = []
        if contrato is None:
            contrato = []
        if selected_sectors is None:
            selected_sectors = []

        # reestablezco la base
        df_shock = df.copy()
        # definicion de hogares en riesgo
        df_shock.loc[(((df_shock['sector'].isin(selected_sectors)) &
                       (df_shock['tipo_empresa'] == empresa)) &
                      ((df_shock['informales'].isin(formalidad)) |
                       (df_shock['cuenta_propia'].isin(contrato)))), 'riesgo'] = 1

        df_shock.riesgo = df_shock.riesgo.fillna(value=0)
        df_shock = update_income(df_shock, shock)

        # ----------------------------
        # 2. Histograma y mediana
        print('Updating Histogram...')
        # ----------------------------

        # clean histogram
        fig_hist.data = []

        # compute kernel
        kernel_shock = gaussian_kde(df_shock.ING_pc_choque_arriendo,
                                    weights=df_shock.fac_exp_ind_12m)

        # update median
        mediana_choque = weighted_median(df_shock,
                                       'ING_pc_choque_arriendo',
                                       'fac_exp_ind_12m')
        texto_mediana = 'Mediana choque: {:,.0f} COP'.format(mediana_choque)

        # modified distribution
        fig_hist.add_trace(go.Scatter(x=xs, y=kernel_shock(xs),
                                      name=u'Distribución Choque',
                                      line_color=naranja,
                                      fill='tozeroy',
                                      fillcolor='rgba(237,177,131,0.5)',
                                      mode='lines'))
        # Original distribution
        fig_hist.add_trace(go.Scatter(x=xs, y=dist_original,
                                      mode='lines',
                                      name=u'Distribución Original',
                                      line=dict(color=black)))

        # ----------------------------
        # 3. Lorenz
        print('Updating Lorenz...')
        # ----------------------------

        # clean figure
        fig_lorenz.data = []

        fig_lorenz.add_trace(go.Scatter(x=[0, 1], y=[0, 1],
                                        mode='lines',
                                        name=u'Igualdad total',
                                        line=dict(color='grey',
                                                  dash="dashdot")))

        # calculate new values
        f_vals_shock, l_vals_shock = qe.lorenz_curve(df_shock.ING_pc_choque_arriendo.to_numpy())

        # sample to plot
        ids = list(range(0, len(f_vals)))
        sample_ids = random.sample(ids, 10000)

        fig_lorenz.add_trace(go.Scatter(x=f_vals_shock[sample_ids],
                                        y=l_vals_shock[sample_ids],
                                        mode='lines',
                                        name=u'Distribución Choque',
                                        line_color=naranja))

        fig_lorenz.add_trace(go.Scatter(x=f_vals[sample_ids],
                                        y=l_vals[sample_ids],
                                        mode='lines',
                                        name=u'Distribución Original',
                                        line_color=black))
        # ----------------------------
        # 4. Poverty
        print('Updating Poverty Measures...')
        # ----------------------------
        pobreza_choque = calculo_pobreza(df_shock, 'ING_pc_choque_arriendo')
        texto_pobreza = u'Índice de pobreza choque: {:.2f}%'.format(pobreza_choque)

    elif action_id == 'reference-lines':
        lines, names = generate_reference_lines(reference_lines, dist_original)
        fig_hist.update_layout(shapes=lines, annotations=names)

    else:
        raise PreventUpdate

    return fig_hist, texto_mediana, fig_lorenz, texto_pobreza

################################
# 4. Run App
################################

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
