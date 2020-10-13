import pandas as pd
import numpy as np

teal = '#3C7A89'
def update_income(df_shock, shock):
    # cambio del ingreso para hogares en riesgo
    df_shock['IMPA_choque'] = df_shock.IMPA_y
    df_shock.loc[(df_shock.riesgo == 1), 'IMPA_choque'] = (1-(shock/100)) * \
                                                          df_shock.IMPA_choque

    # calculo de ingreso per capita
    df_shock.loc[((df_shock.P6430 != 4) & (df_shock.P6430 != 5) & (
            df_shock.P6430 != 6)), 'IT_choque'] = df_shock.loc[:,
                                                  ['IMPA_choque', 'IE_y',
                                                   'ISA_y', 'IOF_y']].sum(
        axis=1, skipna=True)
    df_shock.loc[((df_shock.P6430 == 4) | (
            df_shock.P6430 == 5)), 'IT_choque'] = df_shock.loc[:,
                                                  ['IMPA_choque', 'ISA_y',
                                                   'IOF_y']].sum(axis=1,
                                                                 skipna=True)
    df_shock.loc[(df_shock.P6430 == 6), 'IT_choque'] = df_shock.loc[:,
                                                       ['ISA_y',
                                                        'IOF_y']].sum(axis=1,
                                                                      skipna=True)
    df_shock.loc[((df_shock.DSI == 1) | (
            df_shock.INI == 1)), 'IT_choque'] = df_shock.loc[:,
                                                ['IMDI_y', 'IOF_y']].sum(
        axis=1, skipna=True)

    df_shock.P6050 = pd.to_numeric(df_shock.P6050.replace(' ', np.NaN))
    df_shock.loc[((df_shock.P6050 == 6) | (df_shock.P6050 == 7) | (
            df_shock.P6050 == 8)), 'IT_choque'] = 0
    df_shock.loc[
        ((df_shock.edad < 10) & (df_shock.CLASE_per == 2)), 'IT_choque'] = 0
    df_shock.loc[((df_shock.edad < 12) & (
            df_shock.AREA_per != 12344)), 'IT_choque'] = 0

    # calculo de variables por hogar
    iug_choque = df_shock.groupby(['DIRECTORIO', 'SECUENCIA_P', 'HOGAR'])[
        'IT_choque'].agg(['sum'])

    iug_choque = iug_choque.rename(columns={'sum': 'IUG_choque'})

    # union bases
    df_shock = pd.merge(df_shock, iug_choque,
                        on=['DIRECTORIO', 'SECUENCIA_P', 'HOGAR'], how='left',
                        validate='m:1')
    df_shock[
        'iug_choque_arriendo'] = df_shock.IUG_choque + \
                                 df_shock.arriendo_estimado
    df_shock['ING_pc_choque_arriendo'] = df_shock[
                                             'iug_choque_arriendo'] / \
                                         df_shock.personas_hogar

    return df_shock

def weighted_median(df, x_col, weigths_col):
    df.sort_values(x_col, inplace=True)
    cumsum = df[weigths_col].cumsum()
    cutoff = df[weigths_col].sum() / 2.0
    median = df[x_col][cumsum >= cutoff].iloc[0]
    return median

def generate_reference_lines(reference_lines, dist_original):
    lines = []
    names = []
    if reference_lines is not None:
        if 'Minimum Wage' in reference_lines:
            MW_name = dict(
                x=800000,
                y=max(dist_original),
                text=u'Salario<br>Mínimo')

            MW = dict(
                type='line',
                yref='paper', y0=0, y1=1,
                xref='x', x0=800000, x1=800000,
                line=dict(
                    color="red",
                    width=2,
                    dash="dashdot"))

            lines.append(MW)
            names.append(MW_name)

        if 'Poverty Line' in reference_lines:
            PL_name = dict(
                x=267473,
                y=max(dist_original),
                text=u'Línea de<br>pobreza')

            PL = dict(
                type='line',
                yref='paper', y0=0, y1=1,
                xref='x', x0=267473, x1=267473,
                line=dict(
                    color=teal,
                    width=2,
                    dash="dashdot"))

            lines.append(PL)
            names.append(PL_name)

        if 'Vulnerability Line' in reference_lines:
            VL_name = dict(
                x=401208,
                y=max(dist_original),
                text=u'Línea de<br>vulnerabilidad')

            VL = dict(
                type='line',
                yref='paper', y0=0, y1=1,
                xref='x', x0=401208, x1=401208,
                line=dict(
                    color="#c79408",
                    width=2,
                    dash="dashdot"))

            lines.append(VL)
            names.append(VL_name)

        # crear linea y texto invisible si no se selecciono nada
        if not lines:
            inv_name = dict(x=0, y=0, text='', showarrow=False)
            inv = dict(
                type='line',
                y0=0, y1=1, x0=0, x1=1,
                line=dict(color='white')
            )
            lines.append(inv)
            names.append(inv_name)

    return lines, names

def calculo_pobreza(df, col_ingreso):
    l_ciudad = 294897.29
    l_cab = 294285.32
    l_resto = 175783.22

    df.loc[((df[col_ingreso] < l_resto) &
            (df.CLASE_per == 2) &
            (df.AREA_per == 12344)), 'pobreza_nuevo_arr'] = 1

    df.loc[((df[col_ingreso] < l_cab) &
            (df.CLASE_per == 1) &
            (df.AREA_per == 12344)), 'pobreza_nuevo_arr'] = 1

    df.loc[((df[col_ingreso] < l_ciudad) &
            (df.AREA_per != 12344)), 'pobreza_nuevo_arr'] = 1

    df.pobreza_nuevo_arr = df.pobreza_nuevo_arr.fillna(value=0)

    t_temp = pd.crosstab(df.pobreza_nuevo_arr, df.cat_dom,
                         df.fac_exp_ind_12m, aggfunc='sum',
                         dropna=True)

    t_temp = t_temp.fillna(value=0)
    t_temp = t_temp.append(t_temp.sum().rename('Total'))
    t_temp['Total'] = t_temp.sum(axis=1)
    pobreza = (t_temp.Total.iloc[1]/t_temp.Total.iloc[2])*100

    return pobreza