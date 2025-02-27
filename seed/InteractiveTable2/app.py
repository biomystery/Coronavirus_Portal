import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import re
import plotly.graph_objs as go
import plotly.express as px

app = dash.Dash(__name__)


file_folder = '../data/'
df_default = pd.read_csv(file_folder + 'Ifn_Means.csv')
df = pd.read_csv(file_folder + 'Means.csv')

PAGE_SIZE = 5

app.layout = html.Div(
    className="row",
    children=[
        html.Div(
            dash_table.DataTable(
                id='table-paging-with-graph',
                columns=[
                    {"name": i, "id": i} for i in sorted(df.columns)
                ],
                page_current=0,
                page_size=20,
                page_action='custom',

                filter_action='custom',
                filter_query='',
                sort_action='custom',
                sort_mode='multi',
                sort_by=[],
                editable=True,
        
                #filter_action="native",
                #sort_action="native",
                #sort_mode="multi",
                column_selectable="single",
                row_selectable="multi",
                row_deletable=True,
                selected_columns=[],
                selected_rows=[],
                #page_action="native",
                #page_current= 0,
                #page_size= 10,
            ),
            style={'height': 750, 'overflowY': 'scroll'},
            className='six columns'
        ),
        html.Div(
            id='table-paging-with-graph-container',
            className="five columns"
        )
    ]
)

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                    name_part, value_part = filter_part.split(operator, 1)
                    name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                    value_part = value_part.strip()
                    v0 = value_part[0]
                    if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                        value = value_part[1: -1].replace('\\' + v0, v0)
                    else:
                        try:
                            value = float(value_part)
                        except ValueError:
                            value = value_part

                    # word operators need spaces after them in the filter string,
                    # but we don't want these later
                    return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    Output('table-paging-with-graph', "data"),
    [Input('table-paging-with-graph', "page_current"),
     Input('table-paging-with-graph', "page_size"),
     Input('table-paging-with-graph', "sort_by"),
     Input('table-paging-with-graph', "filter_query")])

def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    
    dff = df

    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            #m = re.search(r'\s+OR\s+',filter_value)
            #if (m):
            #else:
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]
        else:
            dff = dff.loc[dff["Gene"].str.contains("Ifn")]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    return dff.iloc[ 
        page_current*page_size: (page_current + 1)*page_size
    ].to_dict('records')


@app.callback(
    Output('table-paging-with-graph-container', "children"),
    [Input('table-paging-with-graph', "data")])
def update_graph(rows):
    dff = pd.DataFrame(rows)
    #load files or pickles with lookup data
    #read in 74biosets_abridged.csv
    #make list of all genes in header row
    #read each line
    #make dictionary entry
    #where key is Gene_DPI_Strain_Dose
    
    f = open(file_folder + "74biosets_abridged.csv", "r")
    i = 1 #i is file line counter
    genes = [] #pulled from header line
    pdi_age_strain_lookup = {}
    pdi_age_dose_lookup = {}
    for x in f: #x is line in file f
        l = x.split(",")
        if(i == 1):
            genes = l[4:]
        else:
            pdi = l[0]
            age = l[1]
            strain = l[2]
            dose = l[3]
            exp = l[4:]
            pas_key_suffix = str(pdi) + "_" + age + "_" + strain
            pad_key_suffix = str(pdi) + "_" + age + "_" + str(dose)
            #g is counter for expression values in exp
            g = 0
            for gene in genes:
                pas_key = gene + "_" + pas_key_suffix
                pad_key = gene + "_" + pad_key_suffix
                pdi_age_strain_lookup[pas_key] = exp[g]
                pdi_age_dose_lookup[pad_key] = exp[g]
                g = g + 1
        #i is file line counter
        i = i + 1
        
    #make 10 graphs
    #6: 1 and 3 year olds vs 3 strains
    #4: 2 year olds vs 4 dosages
    
    age = "1-young (<10 weeks old)"
    strain = "2-MA15e"
    layout = go.Layout(title='1-young (10 weeks old) & 2-MA15e', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig = go.Figure(layout=layout)
    
    x_axis = ["0.5","1","2","4","7"]
    #make 1 yr old vs 2-MA15e, 3-MA15g, 4MA15

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items(): 
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup: 
                        exp = pdi_age_strain_lookup[pas_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))

    strain = "3-MA15g"
    layout = go.Layout(title='1-young (<10 weeks old) & 3-15MAg', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    
    fig2 = go.Figure(layout=layout)

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                #print(gene)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup:
                        exp = pdi_age_strain_lookup[pas_key]
                        #print(exp)
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig2.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))

    strain = "4-MA15"
    layout = go.Layout(title='1-young (<10 weeks old) & 3-15MAg', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)

    fig3 = go.Figure(layout=layout)

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                #print(gene)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup:
                        exp = pdi_age_strain_lookup[pas_key]
                        #print(exp)
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig3.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))

    age = "3-aged (52 weeks old)"
    strain = "2-MA15e"
    layout = go.Layout(title='3-aged (52 weeks old) & 2-MA15e', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig4 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]
    #make 1 yr old vs 2-MA15e, 3-MA15g, 4MA15

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup:
                        exp = pdi_age_strain_lookup[pas_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig4.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))
    
    strain = "3-MA15g"
    layout = go.Layout(title='3-aged (52 weeks old) & 3-MA15g', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig5 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]
    #make 1 yr old vs 2-MA15e, 3-MA15g, 4MA15

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup:
                        exp = pdi_age_strain_lookup[pas_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig5.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))

    strain = "4-MA15"
    layout = go.Layout(title='3-aged (52 weeks old) & 4-MA15', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig6 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]
    #make 1 yr old vs 2-MA15e, 3-MA15g, 4MA15

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pas_key_suffix = str(pdi) + "_" + age + "_" + strain
                    pas_key = gene + "_" + pas_key_suffix
                    if pas_key in pdi_age_strain_lookup:
                        exp = pdi_age_strain_lookup[pas_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig6.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))
    
    age = "2-adult (20-23 weeks old)"
    dose = "100"
    layout = go.Layout(title='2-adult (20-23 weeks old) & 100 PFU', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig7 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pad_key_suffix = str(pdi) + "_" + age + "_" + str(dose)
                    pad_key = gene + "_" + pad_key_suffix
                    if pad_key in pdi_age_dose_lookup:
                        exp = pdi_age_dose_lookup[pad_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig7.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))

    dose = "1000"
    layout = go.Layout(title='2-adult (20-23 weeks old) & 1000 PFU', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig8 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pad_key_suffix = str(pdi) + "_" + age + "_" + str(dose)
                    pad_key = gene + "_" + pad_key_suffix
                    if pad_key in pdi_age_dose_lookup:
                        exp = pdi_age_dose_lookup[pad_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig8.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))
    
    dose = "10000"
    layout = go.Layout(title='2-adult (20-23 weeks old) & 10000 PFU', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig9 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pad_key_suffix = str(pdi) + "_" + age + "_" + str(dose)
                    pad_key = gene + "_" + pad_key_suffix
                    if pad_key in pdi_age_dose_lookup:
                        exp = pdi_age_dose_lookup[pad_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig9.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))
    
    dose = "100000"
    layout = go.Layout(title='2-adult (20-23 weeks old) & 100000 PFU', xaxis=dict(title='Day Post-Infection'),yaxis=dict(title='AVG Gene Score'), width=600, height=400)
    fig10 = go.Figure(layout=layout)

    x_axis = ["0.5","1","2","4","7"]

    for row in rows:
        i = 1
        gene = "x"
        for key, value in row.items():
            #print (key, value)
            y_series = []
            if(i == 1):
                gene = str(value)
                for pdi in x_axis:
                    pad_key_suffix = str(pdi) + "_" + age + "_" + str(dose)
                    pad_key = gene + "_" + pad_key_suffix
                    if pad_key in pdi_age_dose_lookup:
                        exp = pdi_age_dose_lookup[pad_key]
                        y_series.append(exp)
                exp_data = go.Scatter(x=x_axis,y=y_series)
                fig10.add_trace(go.Scatter(exp_data,name=gene,textposition="top center"))


    return html.Div(
        [   
            dcc.Graph(
                id='g1',
                figure =  fig
            ),
            dcc.Graph(
                id='g2',
                figure =  fig2
            ),
            dcc.Graph(
                id='g3',
                figure =  fig3
            ),
            dcc.Graph(
                id='g4',
                figure =  fig4
            ),
            dcc.Graph(
                id='g5',
                figure =  fig5
            ),
            dcc.Graph(
                id='g6',
                figure =  fig6
            ),
            dcc.Graph(
                id='g7',
                figure =  fig7
            ),
            dcc.Graph(
                id='g8',
                figure =  fig8
            ),
            dcc.Graph(
                id='g9',
                figure =  fig9
            ),
            dcc.Graph(
                id='g10',
                figure =  fig10
            )            
        ]
    )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8049)
