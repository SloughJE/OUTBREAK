import pandas as pd
import numpy as np
import plotly.graph_objects as go


# Organizing the diseases into a dictionary where each disease is mapped to its group or class
disease_groups = {
    "Anthrax": "Anthrax",
    "Arboviral diseases, Chikungunya virus disease": "Arboviral diseases",
    "Arboviral diseases, Eastern equine encephalitis virus disease": "Arboviral diseases",
    "Arboviral diseases, Jamestown Canyon virus disease": "Arboviral diseases",
    "Arboviral diseases, La Crosse virus disease": "Arboviral diseases",
    "Arboviral diseases, Powassan virus disease": "Arboviral diseases",
    "Arboviral diseases, St. Louis encephalitis virus disease": "Arboviral diseases",
    "Arboviral diseases, West Nile virus disease": "Arboviral diseases",
    "Arboviral diseases, Western equine encephalitis virus disease": "Arboviral diseases",
    "Babesiosis": "Babesiosis",
    "Botulism, Foodborne": "Botulism",
    "Botulism, Infant": "Botulism",
    "Botulism, Other (wound & unspecified)": "Botulism",
    "Brucellosis": "Brucellosis",
    "Campylobacteriosis": "Campylobacteriosis",
    "Candida auris, clinical": "Candidiasis",
    "Candida auris, screening": "Candidiasis",
    "Carbapenemase-Producing Organisms (CPO), Total": "Carbapenem-resistant Enterobacteriaceae (CRE)",
    "Chancroid": "Chancroid",
    "Chlamydia trachomatis infection": "Chlamydial infection",
    "Cholera": "Cholera",
    "Coccidioidomycosis, Confirmed": "Coccidioidomycosis",
    "Coccidioidomycosis, Probable": "Coccidioidomycosis",
    "Coccidioidomycosis, total": "Coccidioidomycosis",
    "Cronobacter invasive infection, infants, Confirmed": "Cronobacter infection",
    "Cronobacter invasive infection, infants, Probable": "Cronobacter infection",
    "Cryptosporidiosis": "Cryptosporidiosis",
    "Cyclosporiasis": "Cyclosporiasis",
    "Dengue virus infections, Dengue": "Dengue",
    "Dengue virus infections, Dengue-like illness": "Dengue",
    "Dengue virus infections, Severe dengue": "Dengue",
    "Giardiasis": "Giardiasis",
    "Gonorrhea": "Gonorrhea",
    "Haemophilus influenzae, invasive disease, Age <5 years, Non-b serotype": "Haemophilus influenzae infection",
    "Haemophilus influenzae, invasive disease, Age <5 years, Nontypeable": "Haemophilus influenzae infection",
    "Haemophilus influenzae, invasive disease, Age <5 years, Serotype b": "Haemophilus influenzae infection",
    "Haemophilus influenzae, invasive disease, Age <5 years, Unknown serotype": "Haemophilus influenzae infection",
    "Haemophilus influenzae, invasive disease, All ages, all serotypes": "Haemophilus influenzae infection",
    "Hansen's disease": "Leprosy",
    "Hantavirus infection, non-hantavirus pulmonary syndrome": "Hantavirus infection",
    "Hantavirus pulmonary syndrome": "Hantavirus infection",
    "Hemolytic uremic syndrome post-diarrheal": "Hemolytic uremic syndrome",
    "Hepatitis A, Confirmed": "Hepatitis A",
    "Hepatitis B, acute, Confirmed": "Hepatitis B",
    "Hepatitis B, acute, Probable": "Hepatitis B",
    "Hepatitis B, chronic, Confirmed": "Hepatitis B",
    "Hepatitis B, chronic, Probable": "Hepatitis B",
    "Hepatitis B, perinatal, Confirmed": "Hepatitis B",
    "Hepatitis C, acute, Confirmed": "Hepatitis C",
    "Hepatitis C, acute, Probable": "Hepatitis C",
    "Hepatitis C, chronic, Confirmed": "Hepatitis C",
    "Hepatitis C, chronic, Probable": "Hepatitis C",
    "Hepatitis C, perinatal, Confirmed": "Hepatitis C",
    "Influenza-associated pediatric mortality": "Influenza",
    "Invasive pneumococcal disease, age <5 years, Confirmed": "Pneumococcal disease",
    "Invasive pneumococcal disease, age <5 years, Probable": "Pneumococcal disease",
    "Invasive pneumococcal disease, all ages, Confirmed": "Pneumococcal disease",
    "Invasive pneumococcal disease, all ages, Probable": "Pneumococcal disease",
    "Legionellosis": "Legionellosis",
    "Leptospirosis": "Leptospirosis",
    "Listeriosis, Confirmed": "Listeriosis",
    "Listeriosis, Probable": "Listeriosis",
    "Malaria": "Malaria",
    "Measles, Imported": "Measles",
    "Measles, Indigenous": "Measles",
    "Melioidosis": "Melioidosis",
    "Meningococcal disease, All serogroups": "Meningococcal disease",
    "Meningococcal disease, Other serogroups": "Meningococcal disease",
    "Meningococcal disease, Serogroup B": "Meningococcal disease",
    "Meningococcal disease, Serogroups ACWY": "Meningococcal disease",
    "Meningococcal disease, Unknown serogroup": "Meningococcal disease",
    "Mpox": "Mpox",
    "Mumps": "Mumps",
    "Novel Influenza A virus infections": "Influenza",
    "Pertussis": "Pertussis",
    "Plague": "Plague",
    "Poliomyelitis, paralytic": "Poliomyelitis",
    "Poliovirus infection, nonparalytic": "Poliomyelitis",
    "Psittacosis": "Psittacosis",
    "Q fever, Acute": "Q fever",
    "Q fever, Chronic": "Q fever",
    "Q fever, Total": "Q fever",
    "Rabies, Human": "Rabies",
    "Rubella": "Rubella",
    "Rubella, congenital syndrome": "Rubella",
    "Salmonella Paratyphi infection": "Salmonellosis",
    "Salmonella Typhi infection": "Salmonellosis",
    "Salmonellosis": "Salmonellosis",
    "Severe acute respiratory syndrome-associated coronavirus disease": "SARS",
    "Shiga toxin-producing Escherichia coli (STEC)": "STEC infection",
    "Shigellosis": "Shigellosis",
    "Smallpox": "Smallpox",
    "Streptococcal toxic shock syndrome": "Toxic shock syndrome",
    "Syphilis, Congenital": "Syphilis",
    "Syphilis, Primary and secondary": "Syphilis",
    "Tetanus": "Tetanus",
    "Toxic shock syndrome (other than Streptococcal)": "Toxic shock syndrome",
    "Trichinellosis": "Trichinellosis",
    "Tuberculosis": "Tuberculosis",
    "Tularemia": "Tularemia",
    "Vancomycin-intermediate Staphylococcus aureus": "Staphylococcus aureus infection",
    "Vancomycin-resistant Staphylococcus aureus": "Staphylococcus aureus infection",
    "Varicella disease": "Varicella",
    "Yellow fever": "Yellow fever",
    "Zika virus disease, non-congenital": "Zika virus disease",
    "Arboviral diseases, Jamestown Canyon  virus disease": "Arboviral diseases",
    "Arboviral diseases, La Crosse  virus disease": "Arboviral diseases",
    "Salmonellosis (excluding Salmonella Typhi infection and Salmonella Paratyphi infection)": "Salmonellosis",
    "Vibriosis (any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139), Confirmed": "Vibriosis",
    "Vibriosis (any species of the family Vibrionaceae, other than toxigenic Vibrio cholerae O1 or O139), Probable": "Vibriosis",
    "Viral hemorrhagic fevers, Chapare virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Crimean-Congo hemorrhagic fever virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Ebola virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Guanarito virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Junin virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Lassa virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Lujo virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Machupo virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Marburg virus": "Viral hemorrhagic fevers",
    "Viral hemorrhagic fevers, Sabia virus": "Viral hemorrhagic fevers",
    'Carbapenemase-producing carbapenem-resistant Enterobacteriaceae': 'Carbapenem-resistant Enterobacteriaceae (CRE)',
    'Coccidioidomycosis': 'Coccidioidomycosis',
    'Ehrlichiosis and Anaplasmosis, Anaplasma phagocytophilum infection': 'Ehrlichiosis and Anaplasmosis',
    'Ehrlichiosis and Anaplasmosis, Ehrlichia chaffeensis infection': 'Ehrlichiosis and Anaplasmosis',
    'Ehrlichiosis and Anaplasmosis, Ehrlichia ewingii infection': 'Ehrlichiosis and Anaplasmosis',
    'Ehrlichiosis and Anaplasmosis, Undetermined ehrlichiosis/anaplasmosis': 'Ehrlichiosis and Anaplasmosis',
    'Hepatitis B, acute': 'Hepatitis B',
    'Hepatitis B, perinatal infection': 'Hepatitis B, perinatal',
    'Hepatitis C, perinatal infection': 'Hepatitis C, perinatal',
    'Hepatitis, A, acute': 'Hepatitis A',
    'Hepatitis, B, acute': 'Hepatitis B',
    'Rabies, Animal': 'Rabies',
    'Varicella morbidity': 'Varicella',

}   

disease_details = {
    "Anthrax": {
        "group": "Anthrax",
        "category": "Bacterial",
        "body_system": ["Integumentary", "Respiratory", "Gastrointestinal"],
        "transmission": ["Contact", "Zoonotic"]
    },
    "Arboviral diseases": {
        "group": "Arboviral diseases",
        "category": "Viral",
        "body_system": ["Neurological", "Integumentary"],
        "transmission": ["Vector-borne"]
    },
    "Babesiosis": {
        "group": "Babesiosis",
        "category": "Parasitic",
        "body_system": ["Hematologic"],
        "transmission": ["Vector-borne"]
    },
    "Botulism": {
        "group": "Botulism",
        "category": "Bacterial",
        "body_system": ["Neurological", "Gastrointestinal"],
        "transmission": ["Oral-fecal", "Contact"]
    },
    "Brucellosis": {
        "group": "Brucellosis",
        "category": "Bacterial",
        "body_system": ["Musculoskeletal", "Reproductive"],
        "transmission": ["Contact", "Zoonotic"]
    },
    "Campylobacteriosis": {
        "group": "Campylobacteriosis",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Candidiasis": {
        "group": "Candidiasis",
        "category": "Fungal",
        "body_system": ["Integumentary", "Gastrointestinal"],
        "transmission": ["Contact", "Vertical"]
    },
    "Carbapenem-resistant Enterobacteriaceae (CRE)": {
        "group": "Carbapenem-resistant Enterobacteriaceae (CRE)",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal", "Urinary"],
        "transmission": ["Contact"]
    },
    "Chancroid": {
        "group": "Chancroid",
        "category": "Bacterial",
        "body_system": ["Reproductive"],
        "transmission": ["Sexual"]
    },
    "Chlamydial infection": {
        "group": "Chlamydial infection",
        "category": "Bacterial",
        "body_system": ["Reproductive", "Ocular"],
        "transmission": ["Sexual", "Vertical"]
    },
    "Cholera": {
        "group": "Cholera",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Coccidioidomycosis": {
        "group": "Coccidioidomycosis",
        "category": "Fungal",
        "body_system": ["Respiratory", "Musculoskeletal"],
        "transmission": ["Inhalation"]
    },
    "Cronobacter infection": {
        "group": "Cronobacter infection",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal", "Contact"]
    },
    "Cryptosporidiosis": {
        "group": "Cryptosporidiosis",
        "category": "Parasitic",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Cyclosporiasis": {
        "group": "Cyclosporiasis",
        "category": "Parasitic",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Dengue": {
        "group": "Dengue",
        "category": "Viral",
        "body_system": ["Hematologic", "Integumentary"],
        "transmission": ["Vector-borne"]
    },
    "Giardiasis": {
        "group": "Giardiasis",
        "category": "Parasitic",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Gonorrhea": {
        "group": "Gonorrhea",
        "category": "Bacterial",
        "body_system": ["Reproductive"],
        "transmission": ["Sexual"]
    },
    "Haemophilus influenzae infection": {
        "group": "Haemophilus influenzae infection",
        "category": "Bacterial",
        "body_system": ["Respiratory", "Neurological"],
        "transmission": ["Respiratory", "Contact"]
    },
    "Leprosy": {
        "group": "Leprosy",
        "category": "Bacterial",
        "body_system": ["Integumentary", "Nervous"],
        "transmission": ["Contact"]
    },
    "Hantavirus infection": {
        "group": "Hantavirus infection",
        "category": "Viral",
        "body_system": ["Respiratory", "Cardiovascular"],
        "transmission": ["Inhalation", "Zoonotic"]
    },
    "Hemolytic uremic syndrome": {
        "group": "Hemolytic uremic syndrome",
        "category": "Bacterial",
        "body_system": ["Renal", "Hematologic"],
        "transmission": ["Oral-fecal"]
    },
    "Hepatitis A": {
        "group": "Hepatitis A",
        "category": "Viral",
        "body_system": ["Hepatic"],
        "transmission": ["Oral-fecal"]
    },
    "Hepatitis B": {
        "group": "Hepatitis B",
        "category": "Viral",
        "body_system": ["Hepatic"],
        "transmission": ["Bloodborne", "Sexual", "Vertical"]
    },
    "Hepatitis C": {
        "group": "Hepatitis C",
        "category": "Viral",
        "body_system": ["Hepatic"],
        "transmission": ["Bloodborne", "Sexual", "Vertical"]
    },
    "Influenza": {
        "group": "Influenza",
        "category": "Viral",
        "body_system": ["Respiratory"],
        "transmission": ["Respiratory"]
    },
    "Pneumococcal disease": {
        "group": "Pneumococcal disease",
        "category": "Bacterial",
        "body_system": ["Respiratory"],
        "transmission": ["Respiratory", "Contact"]
    },
    "Legionellosis": {
        "group": "Legionellosis",
        "category": "Bacterial",
        "body_system": ["Respiratory"],
        "transmission": ["Inhalation"]
    },
    "Leptospirosis": {
        "group": "Leptospirosis",
        "category": "Bacterial",
        "body_system": ["Renal", "Hepatic"],
        "transmission": ["Contact", "Waterborne"]
    },
    "Listeriosis": {
        "group": "Listeriosis",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal", "Nervous"],
        "transmission": ["Oral-fecal"]
    },
    "Malaria": {
        "group": "Malaria",
        "category": "Parasitic",
        "body_system": ["Hematologic"],
        "transmission": ["Vector-borne"]
    },
    "Measles": {
        "group": "Measles",
        "category": "Viral",
        "body_system": ["Respiratory", "Integumentary"],
        "transmission": ["Respiratory"]
    },
    "Melioidosis": {
        "group": "Melioidosis",
        "category": "Bacterial",
        "body_system": ["Respiratory", "Cutaneous"],
        "transmission": ["Inhalation", "Contact"]
    },
    "Meningococcal disease": {
        "group": "Meningococcal disease",
        "category": "Bacterial",
        "body_system": ["Nervous"],
        "transmission": ["Respiratory", "Contact"]
    },
    "Mpox": {
        "group": "Mpox",
        "category": "Viral",
        "body_system": ["Integumentary", "Respiratory"],
        "transmission": ["Contact", "Respiratory", "Zoonotic"]
    },
    "Mumps": {
        "group": "Mumps",
        "category": "Viral",
        "body_system": ["Respiratory", "Reproductive"],
        "transmission": ["Respiratory"]
    },
    "Pertussis": {
        "group": "Pertussis",
        "category": "Bacterial",
        "body_system": ["Respiratory"],
        "transmission": ["Respiratory"]
    },
    "Plague": {
        "group": "Plague",
        "category": "Bacterial",
        "body_system": ["Lymphatic", "Respiratory"],
        "transmission": ["Vector-borne", "Contact", "Respiratory"]
    },
    "Poliomyelitis": {
        "group": "Poliomyelitis",
        "category": "Viral",
        "body_system": ["Neurological"],
        "transmission": ["Oral-fecal", "Contact"]
    },
    "Psittacosis": {
        "group": "Psittacosis",
        "category": "Bacterial",
        "body_system": ["Respiratory"],
        "transmission": ["Inhalation"]
    },
    "Q fever": {
        "group": "Q fever",
        "category": "Bacterial",
        "body_system": ["Respiratory", "Hepatic"],
        "transmission": ["Inhalation", "Contact"]
    },
    "Rabies": {
        "group": "Rabies",
        "category": "Viral",
        "body_system": ["Neurological"],
        "transmission": ["Contact", "Zoonotic"]
    },
    "Rubella": {
        "group": "Rubella",
        "category": "Viral",
        "body_system": ["Respiratory", "Integumentary"],
        "transmission": ["Respiratory"]
    },
    "Salmonellosis": {
        "group": "Salmonellosis",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "SARS": {
        "group": "SARS",
        "category": "Viral",
        "body_system": ["Respiratory"],
        "transmission": ["Respiratory", "Contact"]
    },
    "STEC infection": {
        "group": "STEC infection",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Shigellosis": {
        "group": "Shigellosis",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Smallpox": {
        "group": "Smallpox",
        "category": "Viral",
        "body_system": ["Integumentary", "Respiratory"],
        "transmission": ["Respiratory", "Contact"]
    },
    "Syphilis": {
        "group": "Syphilis",
        "category": "Bacterial",
        "body_system": ["Reproductive", "Integumentary"],
        "transmission": ["Sexual", "Vertical"]
    },
    "Tetanus": {
        "group": "Tetanus",
        "category": "Bacterial",
        "body_system": ["Neurological"],
        "transmission": ["Contact"]
    },
    "Toxic shock syndrome": {
        "group": "Toxic shock syndrome",
        "category": "Bacterial",
        "body_system": ["Multiple"],
        "transmission": ["Contact"]
    },
    "Trichinellosis": {
        "group": "Trichinellosis",
        "category": "Parasitic",
        "body_system": ["Musculoskeletal", "Gastrointestinal"],
        "transmission": ["Oral-fecal"]
    },
    "Tuberculosis": {
        "group": "Tuberculosis",
        "category": "Bacterial",
        "body_system": ["Respiratory"],
        "transmission": ["Respiratory"]
    },
    "Tularemia": {
        "group": "Tularemia",
        "category": "Bacterial",
        "body_system": ["Multiple"],
        "transmission": ["Contact", "Vector-borne", "Inhalation"]
    },
    "Varicella": {
        "group": "Varicella",
        "category": "Viral",
        "body_system": ["Integumentary"],
        "transmission": ["Respiratory", "Contact"]
    },
    "Vibriosis": {
        "group": "Vibriosis",
        "category": "Bacterial",
        "body_system": ["Gastrointestinal"],
        "transmission": ["Waterborne"]
    },
    "Viral hemorrhagic fevers": {
        "group": "Viral hemorrhagic fevers",
        "category": "Viral",
        "body_system": ["Multiple"],
        "transmission": ["Contact", "Vector-borne", "Zoonotic"]
    },
    "Yellow fever": {
        "group": "Yellow fever",
        "category": "Viral",
        "body_system": ["Hepatic"],
        "transmission": ["Vector-borne"]
    },
    "Zika virus disease": {
        "group": "Zika virus disease",
        "category": "Viral",
        "body_system": ["Neurological", "Integumentary"],
        "transmission": ["Vector-borne", "Sexual", "Vertical"]
    },
    "Staphylococcus aureus infection": {
        "group": "Staphylococcus aureus infection",
        "category": "Bacterial",
        "body_system": ["Skin", "Respiratory", "Cardiovascular"],
        "transmission": ["Contact"]
    },
    'Ehrlichiosis and Anaplasmosis': {
        "group": "Ehrlichiosis and Anaplasmosis",
        "category": "Bacterial",
        "body_system": ["Hematologic", "Immune"],
        "transmission": ["Vector-borne"]  
    },
}


# Function to map disease to its details
def map_disease_to_details(disease, attribute):
    group = disease_groups.get(disease)
    details = disease_details.get(group, {})
    return details.get(attribute)

def add_disease_info(df):
    df['group'] = df['label'].apply(lambda x: map_disease_to_details(x, 'group'))
    df['category'] = df['label'].apply(lambda x: map_disease_to_details(x, 'category'))
    df['body_system'] = df['label'].apply(lambda x: map_disease_to_details(x, 'body_system'))
    df['transmission'] = df['label'].apply(lambda x: map_disease_to_details(x, 'transmission'))

    df['body_system'] = df['body_system'].apply(lambda x: x if isinstance(x, list) else [x])
    df['transmission'] = df['transmission'].apply(lambda x: x if isinstance(x, list) else [x])
    return df


def bar_chart_counts(counts_df, count_type_title="Pathogen", color="blue",
                     note_text="*Each instance of the same disease across different states is counted separately and may belong to multiple categories"):
    
    outbreak_counts = counts_df.sort_values()

    if color == "blue":
        bar_color = 'rgb(31, 119, 180)'  
    elif color == "green":
        bar_color = 'rgb(44, 160, 44)'  
    elif color == "purple":
        bar_color = 'rgb(148, 103, 189)'  

    fig = go.Figure(data=[go.Bar(
        y=outbreak_counts.index,  
        x=outbreak_counts.values,  
        orientation='h', 
        marker_color=bar_color  
    )])

    fig.update_layout(
        title=f"{count_type_title}",
        yaxis_title="",
        xaxis_title="count of potential outbreaks",
        template='plotly_dark', 
        title_font_size=22,  
        title_x=0.5,  
        title_y=0.9,  
        paper_bgcolor='black',
        plot_bgcolor='black',
    )

    fig.update_layout(
        annotations=[
            dict(
                x=0.5,
                y=-0.25,  
                xref="paper",
                yref="paper",
                text=f"{note_text}",
                showarrow=False,
                font=dict(size=10, color="white"), 
            )
        ]
    )

    return fig