import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import tempfile
import zipfile
import calendar
import locale
from datetime import datetime, timedelta
from data_processor import process_data
from pdf_generator import generate_pdf
from utils import format_currency, to_float, calculate_period_dates

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Generatore Fogli Paga",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tentativo di impostare la lingua italiana per i mesi
# Questo aiuta a visualizzare i nomi dei mesi in italiano nella UI
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')
    except:
        pass  # Fallback alla lingua di sistema se l'italiano non è disponibile

# Funzione per ottenere i nomi dei mesi in italiano
def get_italian_month_name(month_num):
    """
    Restituisce il nome del mese in italiano dato il suo numero (1-12)
    Se non trova corrispondenza, ritorna il nome dal modulo calendar
    
    Args:
        month_num (int): Numero del mese (1=Gennaio, 12=Dicembre)
        
    Returns:
        str: Nome del mese in italiano
    """
    italian_months = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    return italian_months.get(month_num, calendar.month_name[month_num])

# Definizione dei colori per l'interfaccia utente
primary_color = "#007AFF"  # Blu principale (stile Apple)
secondary_color = "#F5F5F7"  # Grigio chiaro per sfondi secondari
dark_grey = "#333333"  # Grigio scuro per testi

# Personalizzazione CSS dell'interfaccia utente
# Questo codice definisce lo stile visuale dell'app (colori, bottoni, layout)
st.markdown(f"""
    <style>
    .main .block-container {{
        max-width: 1200px;
        padding: 2rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    h1, h2, h3, h4 {{
        font-family: 'SF Pro Display', 'Helvetica Neue', sans-serif;
        color: {dark_grey};
    }}
    .stButton>button {{
        background-color: {primary_color};
        color: white;
        font-weight: 500;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }}
    .stButton>button:hover {{
        background-color: #0062cc;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    .stDownloadButton>button {{
        background-color: {primary_color};
        color: white;
        font-weight: 500;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }}
    .stDownloadButton>button:hover {{
        background-color: #0062cc;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    .stUploadButton>button {{
        border-color: {primary_color};
        color: {primary_color};
    }}
    .stProgress .st-bo {{
        background-color: {primary_color};
    }}
    .sidebar .sidebar-content {{
        background-color: {secondary_color};
    }}
    </style>
""", unsafe_allow_html=True)

# Titolo principale dell'app
st.markdown(f"""
    <h1 style='text-align: center; margin-bottom: 1.5rem;'>
        Generatore Fogli Paga
    </h1>
""", unsafe_allow_html=True)

# Barra laterale con istruzioni per l'utente
with st.sidebar:
    # Titolo della sezione istruzioni
    st.markdown(f"""
    <h3 style='color: {primary_color};'>Istruzioni</h3>
    """, unsafe_allow_html=True)
    
    # Elenco di passi da seguire
    st.markdown("""
    1. Seleziona il mese e l'anno di elaborazione
    2. Carica il file con i dati di paga (equivalente a 'incolla qui')
    3. Genera e scarica i PDF delle buste paga
    """)
    
    # Box informativo sui file supportati
    st.markdown(f"""
    <div style="margin-top: 2rem; padding: 1rem; background-color: rgba(0, 122, 255, 0.05); border-radius: 5px; border-left: 3px solid {primary_color};">
        <h3 style='color: {primary_color}; margin-top: 0;'>Informazioni sui File</h3>
        <p style="font-size: 0.9rem;">
            <strong>File Dati Paga:</strong> Carica il tracciato di CL scaricabile dal campo (05>07>11). Questo file contiene i dati dei dipendenti e delle aziende.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Sezione per la selezione del periodo di elaborazione
st.markdown(f"""
    <div style="padding: 1.5rem; background-color: white; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <h2 style="margin-top: 0; color: {primary_color};">Selezione Periodo</h2>
    </div>
""", unsafe_allow_html=True)

# Layout a due colonne per selezionare anno e mese
col1, col2 = st.columns(2)
with col1:
    # Selettore anno: mostra 5 anni precedenti e 2 anni futuri rispetto all'anno corrente
    current_year = datetime.now().year
    year_options = list(range(current_year - 5, current_year + 2))
    selected_year = st.selectbox("Anno", year_options, index=5)  # Default: anno corrente

with col2:
    # Selettore mese: mostra i nomi dei mesi in italiano
    italian_month_names = [get_italian_month_name(i) for i in range(1, 13)]
    current_month = datetime.now().month - 1  # -1 perché gli indici partono da 0
    selected_month = st.selectbox("Mese", italian_month_names, index=current_month)
    selected_month_idx = italian_month_names.index(selected_month) + 1  # +1 perché i mesi iniziano da 1

# Calcola le date di inizio e fine del mese selezionato
# Utile per generare le informazioni sui periodi nei PDF
start_date = datetime(selected_year, selected_month_idx, 1)
end_date = datetime(selected_year, selected_month_idx, calendar.monthrange(selected_year, selected_month_idx)[1])

# Sezione per il caricamento del file
st.markdown(f"""
    <div style="padding: 1.5rem; background-color: white; border-radius: 10px; margin: 1.5rem 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <h2 style="margin-top: 0; color: {primary_color};">Caricamento File</h2>
    </div>
""", unsafe_allow_html=True)

# Descrizione del tipo di file da caricare
st.markdown(f"""
    <div style="background-color: rgba(0, 122, 255, 0.05); padding: 1rem; border-radius: 5px; margin-bottom: 0.5rem;">
        <p style="margin: 0; font-size: 0.9rem;">File dati paga (tracciato di CL scaricabile dal campo 05>07>11)</p>
    </div>
""", unsafe_allow_html=True)

# Widget per il caricamento del file (supporta Excel e CSV)
payroll_file = st.file_uploader("Seleziona file", type=["xlsx", "xls", "csv"], key="payroll", label_visibility="collapsed")

# Process file when uploaded
if payroll_file:
    try:
        # Read payroll file
        if payroll_file.name.endswith(('.xlsx', '.xls')):
            payroll_data = pd.read_excel(payroll_file)
        elif payroll_file.name.endswith('.csv'):
            payroll_data = pd.read_csv(payroll_file, sep=None, engine='python')
        
        # Create date_info dict based on selected period
        manual_date_info = {
            "period": f"{selected_month} {selected_year}",
            "italian_month": selected_month.lower(),  # Nome mese in italiano per il nome della cartella
            "start_date": start_date.strftime("%d/%m/%Y"),
            "end_date": end_date.strftime("%d/%m/%Y"),
            "min_date": start_date,
            "max_date": end_date
        }
        
        # Process data with selected period info
        processed_data, date_info = process_data(payroll_data, manual_date_info)
        
        if processed_data is not None and not processed_data.empty:
            st.markdown(f"""
                <div style="padding: 0.75rem; background-color: #f0f9ff; border-left: 4px solid {primary_color}; border-radius: 4px; margin: 1rem 0;">
                    <h3 style="margin: 0; color: {primary_color};">✓ Dati elaborati con successo!</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Display processing information in a card
            st.markdown(f"""
                <div style="padding: 1.5rem; background-color: white; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 1.5rem;">
                    <h3 style="margin-top: 0; color: {primary_color};">Informazioni Periodo</h3>
                    <p><strong>Periodo:</strong> {date_info['period']}</p>
                    <p><strong>Dal:</strong> {date_info['start_date']}</p>
                    <p><strong>Al:</strong> {date_info['end_date']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Generate PDFs section
            st.markdown(f"""
                <div style="padding: 1.5rem; background-color: white; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <h2 style="margin-top: 0; color: {primary_color};">Generazione PDF</h2>
                    <p>Cliccando sul pulsante qui sotto verranno generati i PDF per tutti gli operatori presenti nei dati.</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Generate PDFs button in column for centering
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                generate_button = st.button("Genera PDF", use_container_width=True)
                
            if generate_button:
                # Create a temporary directory to store the PDFs
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Create a subfolder similar to the VBA macro: "Fogli paghe_<mese>"
                    pdf_folder = os.path.join(temp_dir, f"Fogli_paghe_{date_info['italian_month']}")
                    os.makedirs(pdf_folder, exist_ok=True)
                    
                    # Group by employee
                    employees = processed_data['Operatore'].unique()
                    
                    # Progress bar with card styling
                    st.markdown(f"""
                        <div style="padding: 1.5rem; background-color: white; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-top: 1.5rem;">
                            <h3 style="margin-top: 0; color: {primary_color};">Progresso Generazione</h3>
                    """, unsafe_allow_html=True)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Generate PDF for each employee
                    pdf_files = []
                    for i, employee in enumerate(employees):
                        status_text.markdown(f"""
                            <div style="padding: 0.5rem; border-radius: 5px; margin-bottom: 0.5rem; text-align: center;">
                                <p style="margin: 0;"><strong>Generazione PDF per</strong>: {employee}...</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Filter data for this employee
                        employee_data = processed_data[processed_data['Operatore'] == employee]
                        
                        # Generate PDF with naming convention from the macro
                        employee_name = str(employee).replace(' ', '_')
                        pdf_path = os.path.join(pdf_folder, f"Report_{employee_name}.pdf")
                        generate_pdf(employee_data, pdf_path, date_info)
                        pdf_files.append(pdf_path)
                        
                        # Update progress
                        progress_bar.progress((i + 1) / len(employees))
                    
                    status_text.markdown(f"""
                        <div style="padding: 0.75rem; background-color: #f0fff0; border-left: 4px solid #00aa00; border-radius: 4px; margin: 1rem 0; text-align: center;">
                            <h3 style="margin: 0; color: #00aa00;">✓ Generazione PDF completata!</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)  # Chiude il div di progresso
                    
                    # Create zip file containing all PDFs with the folder structure
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for pdf_path in pdf_files:
                            # Include folder structure in zip
                            arc_name = os.path.join(os.path.basename(pdf_folder), os.path.basename(pdf_path))
                            zip_file.write(pdf_path, arc_name)
                    
                    # Reset buffer position
                    zip_buffer.seek(0)
                    
                    # Create download button using the naming convention from the macro
                    st.markdown(f"""
                        <div style="padding: 1.5rem; background-color: white; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-top: 1.5rem; text-align: center;">
                            <h3 style="margin-top: 0; color: {primary_color};">Download</h3>
                            <p>Tutti i PDF sono stati generati e compressi in un unico file ZIP.</p>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="Scarica tutti i PDF",
                            data=zip_buffer,
                            file_name=f"Fogli_paghe_{date_info['italian_month']}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    
                    st.markdown("</div>", unsafe_allow_html=True)  # Close the download div
        else:
            st.error("Non è stato possibile elaborare i dati. Verifica che il file sia nel formato corretto.")
    except Exception as e:
        st.error(f"Si è verificato un errore durante l'elaborazione: {str(e)}")
