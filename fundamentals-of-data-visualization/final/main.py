import altair as alt
import pandas as pd
from dateutil.parser import parse
import os

# data from https://luftdaten.berlin.de/station/mc174?period=1m&timespan=custom&start%5Bdate%5D=01.11.2017&end%5Bdate%5D=30.11.2022
df = pd.read_csv('ber_mc174_20171101-20221130.csv', sep=';', header=1, skiprows=[2, 3])
df.columns = ['date', 'PM10', 'PM2.5', 'NO2', 'NO', 'NOx', 'O3', 'Benzene', 'Toulene', 'CO',  'SO2']

# Parse dates written in German
monthsReplace = {'Mär': 'Mar', 'Mai': 'May','Okt': 'Oct','Dez': 'Dec'}
df['date'] = pd.to_datetime(df['date'].replace(monthsReplace, regex=True), format='%b %Y')

# Create normalized series
pollutant_columns = df.columns[1:]
df[pollutant_columns] = (df[pollutant_columns] - df[pollutant_columns].min()) / (df[pollutant_columns].max() - df[pollutant_columns].min())

# Transform so we have data in one column (value) and type of data (pollutant) in another.
df = df.melt(id_vars='date', var_name='pollutant', value_name='value')

# Unique parts of two charts specified
dataCharts = [(
    alt.Chart(df).mark_area().encode(
        x='date',
        y=alt.Y('value').stack("normalize"),
        color='pollutant',
    ),
    'chart_correlation_over_time.html'
 ),
 (
     alt.Chart(df).mark_line().encode(
         x='date',
         y='mean(value)'
     ),
     'chart_air_quality_over_time.html'
 )
]

# Generate charts given definitions
for (dataChart, filename) in dataCharts:
    selection = alt.selection_point(encodings=['color'])
    
    dataChart = (
        dataChart.properties(width=2560, height=1280)
                 .transform_filter(selection)
                 .interactive()
    )

    startOfPandemicDf = pd.DataFrame({'x': [parse('2019-11-01')]})
    startOfPandemicText = alt.Chart(startOfPandemicDf).mark_text(dy=-20).encode(
        x='x',
        y=alt.value(1280),
        text=alt.value("Start of Pandemic"),
        size=alt.value(33),
        color=alt.value("red"),
        fill=alt.value("red")
    )
    startOfPandemicLine = alt.Chart(startOfPandemicDf).mark_rule().encode(
        x='x',
        tooltip=alt.Tooltip("x"),
        size=alt.value(5))
    
    legend = alt.Chart(df).mark_rect().encode(
        y=alt.Y('pollutant', axis=alt.Axis(title='Pollutants')),
        color=alt.condition(selection, 'pollutant', alt.value('lightgray'), legend=None),
        size=alt.value(250)
    ).add_params(selection)
    
    chart = (dataChart + startOfPandemicLine + startOfPandemicText) | legend

    path = "./output/"
    if not os.path.exists(path):
        os.makedirs(path)
    chart.save(path + filename)
