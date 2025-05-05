import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import locale
import calendar

def format_currency(value):
    """
    Formatta un numero come stringa di valuta (€ X.XXX,XX).
    
    Questa funzione prende un valore numerico e lo converte in una stringa
    formattata come valuta euro, utilizzando la notazione italiana
    (es. € 1.234,56 invece di € 1,234.56).
    
    Parametri:
        value: Il valore numerico da formattare
        
    Restituisce:
        str: Stringa formattata come valuta
    """
    try:
        # Try to set Italian locale for proper formatting
        try:
            locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'it_IT')
            except:
                # Fallback if Italian locale is not available
                pass
        
        # Convert to float first
        val = to_float(value)
        
        # Format with Euro symbol
        return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        # Return original value if formatting fails
        return str(value)

def to_float(value):
    """
    Converte un valore in float, gestendo diversi formati di numeri.
    
    Questa funzione è progettata per gestire vari formati di numeri,
    inclusi quelli con separatore decimale come virgola (formato italiano)
    o punto (formato inglese), e quelli con simboli di valuta.
    
    Parametri:
        value: Il valore da convertire
        
    Restituisce:
        float: Valore convertito o 0.0 se la conversione fallisce
    """
    if pd.isna(value):
        return 0.0
    
    try:
        # Try direct conversion
        return float(value)
    except (ValueError, TypeError):
        if isinstance(value, str):
            # Handle European number format (comma as decimal separator)
            try:
                return float(value.replace(".", "").replace(",", "."))
            except (ValueError, TypeError):
                # Remove currency symbols and try again
                clean_value = value.replace("€", "").replace("$", "").strip()
                try:
                    return float(clean_value.replace(".", "").replace(",", "."))
                except (ValueError, TypeError):
                    return 0.0
        return 0.0

def calculate_period_dates(df, date_columns):
    """
    Calcola le date di inizio e fine periodo basandosi sui dati.
    
    Questa funzione cerca di estrarre le date minime e massime dai dati
    per determinare il periodo di riferimento. Se non trova date valide,
    utilizza il mese corrente come periodo predefinito.
    
    Parametri:
        df (pd.DataFrame): DataFrame contenente i dati
        date_columns (list): Lista di potenziali nomi di colonne contenenti date
        
    Restituisce:
        dict: Dizionario con le informazioni sul periodo
            {
                'period': Stringa descrittiva del periodo (es. "Aprile 2025"),
                'start_date': Data di inizio in formato "gg/mm/aaaa",
                'end_date': Data di fine in formato "gg/mm/aaaa",
                'min_date': Oggetto datetime con la data minima,
                'max_date': Oggetto datetime con la data massima,
                'italian_month': Nome del mese in italiano, minuscolo
            }
    """
    min_date = None
    max_date = None
    
    # Try to find date columns and extract min/max dates
    for col in date_columns:
        if col in df.columns:
            series = pd.to_datetime(df[col], errors='coerce')
            if not series.isna().all():
                col_min = series.min()
                col_max = series.max()
                
                if min_date is None or col_min < min_date:
                    min_date = col_min
                
                if max_date is None or col_max > max_date:
                    max_date = col_max
    
    # If no valid dates found, use current month
    if min_date is None:
        now = datetime.now()
        min_date = datetime(now.year, now.month, 1)
        max_date = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
    
    # Format dates
    month_name = min_date.strftime("%B").capitalize()
    year = min_date.year
    
    # If the period spans multiple months, use the range
    if min_date.month != max_date.month or min_date.year != max_date.year:
        period = f"{min_date.strftime('%B %Y')} - {max_date.strftime('%B %Y')}"
    else:
        period = f"{month_name} {year}"
    
    # Format dates for display
    start_date = min_date.strftime("%d/%m/%Y")
    end_date = max_date.strftime("%d/%m/%Y")
    
    # Get Italian month name for folder naming
    italian_months = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile",
        5: "maggio", 6: "giugno", 7: "luglio", 8: "agosto",
        9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    italian_month = italian_months.get(min_date.month, month_name.lower())
    
    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "min_date": min_date,
        "max_date": max_date,
        "italian_month": italian_month
    }
