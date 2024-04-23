import dash
import dash_bootstrap_components as dbc
from dash import html
from src.tabs.info_helper import *


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])

main_section_style = {
    'font-size': '22px',  
    'background-color': '#C06070',  
    'color': 'white',  
    'textAlign':'left',
    'textJustify':'left'
}

sub_section_style = {
    'font-size': '22px', 
    'background-color': '#F08080',  
    'color': 'white',
    'textAlign':'left',
    'textJustify':'left'
}

# Function to create a collapsible card
def create_collapsible_card(header_id, collapse_id, title, content, header_style=sub_section_style, is_main=False):
    if is_main:
        button = dbc.Button(title, color="link", className="text-left", id=header_id, style={'font-size': '22px', 'color': 'white'})
    else:
        button = dbc.Button(title, color="link", className="text-left", id=header_id, style={'font-size': '22px', 'color': 'white'})
    
    card = dbc.Card([
        dbc.CardHeader(button, style=header_style),
        dbc.Collapse(
            dbc.CardBody(content),
            id=collapse_id,
        )
    ], className="mb-4")
    
    return card

def info_view_tab_layout():
    
    layout = dbc.Container([
        
        html.Div([
        # Dashboard Information Section with Enhanced "UnHealth Score" Highlight
        create_collapsible_card("collapse-button-dashboard-info", "collapse-dashboard-info", dashboard_info_title, [
            html.P([
                html.Strong("Dashboard Purpose:"), 
                "\n1) Identify weekly 'Potential Outbreaks' and 'Ongoing Potential Outbreaks' of Nationally Notifiable Diseases automatically.\
                \n2) Provide supporting details of the diseases such as historical case counts, pathogen type, affected bodily system, and transmission type.\
                \n\n",

                html.Strong("Important Aspects of the Dashboard:\n"),
                html.Strong("Automatic Weekly Data Retrieval"),
                ": New data from the CDC NNDSS API is updated weekly when available.\n",
                html.Strong("Automatic Weekly Model Retraining"),
                ": When new data is available, the Potential Outbreak Identification Model is retrained with the new data automatically.\n\n",
                
                html.Strong("Definitions:\n"),
                html.Strong("Notifiable Disease"),
                ": The ",
                html.A("CDC", href="https://www.cdc.gov/nchs/hus/sources-definitions/notifiable-disease.html", target="_blank"),
                 " defines this as 'a disease that, when diagnosed, requires health providers (usually by law) to report to state or local public health officials. \
                Notifiable diseases are of public interest by reason of their contagiousness, severity, or frequency.' The list of nationally notifiable diseases is determined by the Centers for \
                    Disease Control and Prevention (CDC) in collaboration with the Council of State and Territorial Epidemiologists (CSTE)\n\n",
                html.Strong("Potential Outbreak"),
                ": an identification of a possible future disease outbreak by our model. This is not meant to identify an actual outbreak of a disease, rather it should be thought of as an early\
                      warning that a disease may develop into an outbreak in the future. The user can selected the desired model certainty. See the Potential Outbreaks Model section for more information.\
                      Note that there is no single specific mathematical definition of an outbreak of a disease. The ",
                html.A("WHO", href="https://www.emro.who.int/health-topics/disease-outbreaks/index.html", target="_blank"),
                " defines an outbreak as the occurrence of cases of a disease in excess of what would normally be expected in a defined community, geographical area or season.\n\n",
                html.Strong("Ongoing Potential Outbreak"),
                ": if a specific disease in a specific state or territory has been identified as a potential outbreak for at least 2 weeks in a row it is considered an 'ongoing potential outbreak'. \
                    This indicates a higher likelihood that this could be an actual outbreak.\n\n",
                html.Strong("Resolved Potential Outbreak"),
                ": if a specific disease was identified as a potential outbreak in week 1, but then it week 2 is not identified as a potential outbreak, it is considered resolved. \
                    This indicates a the potential outbreak did not develop into an actual outbreak.\n"
            ], style={'white-space': 'pre-line'}),

            html.Div([
                html.Span("Developed by ", style={'fontSize': '18px'}),
                html.A(developed_by, href='https://www.jsdatascience.com/', target="_blank", style={'fontSize': '18px'}),
                #html.Div([
                #    html.A("Dashboard GitHub Repo", href="https://github.com/SloughJE/UnHealth_Dashboard", target="_blank", 
                #        style={'fontSize': '18px', 'marginTop': '10px', 'display': 'block'})  
                #], style={'marginTop': '10px'}),
            ]),
        ], header_style=main_section_style, is_main=True),
        
        # Tab Information Section
        create_collapsible_card("collapse-button-tab-info", "collapse-tab-info", tab_information_title, [
            html.H4(summary_tab_title, className="mt-4"),
            html.P(summary_tab_data, style={'white-space': 'pre-line'}),

            html.H4(profiles_tab_title, className="mt-4"),
            html.P(profiles_tab_data, style={'white-space': 'pre-line'}),

        
            html.H4(disease_tab_title, className="mt-4"),
            html.P(disease_tab_data, style={'white-space': 'pre-line'}),
    
            html.H4(outbreaks_tab_title, className="mt-4"),
            html.P(outbreaks_tab_data, style={'white-space': 'pre-line'}),

        ], header_style=main_section_style, is_main=True),

        # Data Sources Section
        create_collapsible_card("collapse-button-data-sources", "collapse-data-sources", data_title, [
            html.H4(data_source_title, className="mt-4"),
            html.P(data_source_text, style={'white-space': 'pre-line'}),
            html.A("CDC NNDSS API", href="https://dev.socrata.com/foundry/data.cdc.gov/x9gk-5huc", target="_blank"),
        ], header_style=main_section_style, is_main=True),

        create_collapsible_card("collapse-button-modeling", "collapse-modeling", modeling_title, [

                create_collapsible_card("collapse-button-modeling-text", "collapse-modeling-text", modeling_subtitle, [
                    html.P(modeling_text),
                    html.A("DeepAR Model Information", href="https://docs.aws.amazon.com/sagemaker/latest/dg/deepar.html", target="_blank"),
                ], header_style=sub_section_style),

                create_collapsible_card("collapse-button-automated", "collapse-automated", automated_title, [
                    html.P(automated_text),
                ], header_style=sub_section_style),
            ], header_style=main_section_style, is_main=True),

        ], style={'paddingTop':'20px'})
        ], fluid=True)
    
    return layout
