#!/usr/bin/env python3
"""
Parser RFEN per CN Caballa
Extreu partits passats i futurs de la web de la RFEN
Versió 1.2 - Correcció pròxims partits sense resultats
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

# ============================================
# CONFIGURACIÓ
# ============================================
TEAM_ID = "14488"  # CN Caballa
TEAM_NAME = "C.n. Caballa - Ciudad De Ceuta"
BASE_URL = "https://rfen.es/especialidades/waterpolo/equipo"

# Ubicacions de piscines (coordenades de Google Maps)
POOL_LOCATIONS = {
    "C.n. Caballa - Ciudad De Ceuta": {
        "name": "Piscina Lorena Miranda",
        "city": "Ceuta",
        "lat": 35.8893,
        "lng": -5.3198
    },
    "C.n. Terrassa": {
        "name": "Piscina Municipal Can Xarau",
        "city": "Terrassa",
        "lat": 41.5630,
        "lng": 2.0082
    },
    "C.n. Barcelona": {
        "name": "Club Natació Barcelona",
        "city": "Barcelona",
        "lat": 41.3851,
        "lng": 2.1923
    },
    "C.e. Mediterrani": {
        "name": "CE Mediterrani",
        "city": "Barcelona",
        "lat": 41.3879,
        "lng": 2.1942
    },
    "Solartradex C.n. Mataró": {
        "name": "Piscina Municipal Mataró",
        "city": "Mataró",
        "lat": 41.5381,
        "lng": 2.4445
    },
    "Santa Cruz Tenerife Echeyde": {
        "name": "Piscina Acidalio Lorenzo",
        "city": "Santa Cruz de Tenerife",
        "lat": 28.4636,
        "lng": -16.2518
    },
    "C. Encinas De Boadilla": {
        "name": "Piscina Municipal Boadilla",
        "city": "Boadilla del Monte",
        "lat": 40.4058,
        "lng": -3.8756
    },
    "C.n. Sant Andreu": {
        "name": "Piscina Municipal Trinitat Vella",
        "city": "Barcelona",
        "lat": 41.4456,
        "lng": 2.1892
    },
    "C.n. Atlètic-Barceloneta": {
        "name": "Club Natació Atlètic-Barceloneta",
        "city": "Barcelona",
        "lat": 41.3809,
        "lng": 2.1897
    },
    "Real Canoe N.c.": {
        "name": "Real Canoe NC",
        "city": "Madrid",
        "lat": 40.4538,
        "lng": -3.6745
    },
    "C.n. Sabadell": {
        "name": "Piscina Can Llong",
        "city": "Sabadell",
        "lat": 41.5500,
        "lng": 2.1028
    }
}

def fetch_page(url):
    """Descarrega una pàgina amb encoding correcte"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'  # Forçar UTF-8
    response.raise_for_status()
    return response.text

def safe_int(elem):
    """Converteix un element a int si és possible, sinó retorna 0"""
    if not elem:
        return 0
    text = elem.get_text(strip=True)
    return int(text) if text and text.isdigit() else 0

def parse_match_block(block):
    """Parseja un bloc de partit"""
    try:
        # Data ISO del meta
        start_date = block.find('time', itemprop='startDate')
        iso_date = start_date.get('content') if start_date else None
        
        # Jornada
        jornada_elem = block.find('div', class_='RFEN_MatchRowTimeContainer_date')
        jornada_text = jornada_elem.find('span').get_text(strip=True) if jornada_elem else ""
        jornada_match = re.search(r'Jornada\s+(\d+)', jornada_text)
        jornada = int(jornada_match.group(1)) if jornada_match else None
        
        # Data i hora visible
        hour_elem = block.find('div', class_='RFEN_MatchRowTimeContainer_hour')
        datetime_text = hour_elem.find('span').get_text(strip=True) if hour_elem else ""
        
        # Estat
        status_elem = block.find('div', class_='RFEN_MatchRowStatusContainer')
        status = status_elem.get_text(strip=True) if status_elem else "Pendiente"
        
        # Equips
        teams = block.find_all('div', class_='RFEN_MatchRowTeamContainer')
        
        if len(teams) < 2:
            return None
        
        # ========== EQUIP LOCAL ==========
        local_name_elem = teams[0].find('div', class_='RFEN_MatchRowName')
        local_name = local_name_elem.get_text(strip=True) if local_name_elem else ""
        local_logo = teams[0].find('img', class_='RFEN_MatchRowImage')
        local_logo_url = local_logo.get('src') if local_logo else ""
        
        # Resultat local (pot estar buit per futurs partits)
        local_result_elem = teams[0].find('div', class_='RFEN_MatchRowResultFinal')
        local_score_text = local_result_elem.get_text(strip=True) if local_result_elem else ""
        local_score = int(local_score_text) if local_score_text and local_score_text.isdigit() else None
        
        # Parcials local
        local_p1 = teams[0].find('div', class_='RFEN_MatchRowResultP1')
        local_p2 = teams[0].find('div', class_='RFEN_MatchRowResultP2')
        local_p3 = teams[0].find('div', class_='RFEN_MatchRowResultP3')
        local_p4 = teams[0].find('div', class_='RFEN_MatchRowResultP4')
        
        local_quarters = {
            'q1': safe_int(local_p1),
            'q2': safe_int(local_p2),
            'q3': safe_int(local_p3),
            'q4': safe_int(local_p4)
        }
        
        # ========== EQUIP VISITANT ==========
        away_name_elem = teams[1].find('div', class_='RFEN_MatchRowName')
        away_name = away_name_elem.get_text(strip=True) if away_name_elem else ""
        away_logo = teams[1].find('img', class_='RFEN_MatchRowImage')
        away_logo_url = away_logo.get('src') if away_logo else ""
        
        # Resultat visitant
        away_result_elem = teams[1].find('div', class_='RFEN_MatchRowResultFinal')
        away_score_text = away_result_elem.get_text(strip=True) if away_result_elem else ""
        away_score = int(away_score_text) if away_score_text and away_score_text.isdigit() else None
        
        # Parcials visitant
        away_p1 = teams[1].find('div', class_='RFEN_MatchRowResultP1')
        away_p2 = teams[1].find('div', class_='RFEN_MatchRowResultP2')
        away_p3 = teams[1].find('div', class_='RFEN_MatchRowResultP3')
        away_p4 = teams[1].find('div', class_='RFEN_MatchRowResultP4')
        
        away_quarters = {
            'q1': safe_int(away_p1),
            'q2': safe_int(away_p2),
            'q3': safe_int(away_p3),
            'q4': safe_int(away_p4)
        }
        
        # Determinar si CN Caballa és local o visitant
        is_home = TEAM_NAME.lower() in local_name.lower() or "caballa" in local_name.lower()
        
        # Obtenir ubicació (piscina de l'equip local)
        location = get_location(local_name)
        
        return {
            'jornada': jornada,
            'date': datetime_text,
            'iso_date': iso_date,
            'status': status,
            'is_home': is_home,
            'local': {
                'name': local_name,
                'logo': local_logo_url,
                'score': local_score,
                'quarters': local_quarters
            },
            'away': {
                'name': away_name,
                'logo': away_logo_url,
                'score': away_score,
                'quarters': away_quarters
            },
            'location': location
        }
        
    except Exception as e:
        print(f"⚠️ Error parsejant bloc: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_location(team_name):
    """Obté la ubicació d'un equip"""
    team_lower = team_name.lower()
    for key, loc in POOL_LOCATIONS.items():
        if key.lower() in team_lower or team_lower in key.lower():
            return loc
    # Si no trobem, retornar None però avisar
    print(f"⚠️ Ubicació no trobada per: {team_name}")
    return None

def parse_partidos(url):
    """Parseja una pàgina de partits"""
    print(f"📥 Descarregant: {url}")
    
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    matches = []
    match_blocks = soup.find_all('div', class_='RFEN_MatchRowContainer')
    
    print(f"   Trobats {len(match_blocks)} partits")
    
    for block in match_blocks:
        match_data = parse_match_block(block)
        if match_data:
            matches.append(match_data)
    
    return matches
def parse_clasificacion():
    """Parseja la classificació"""
    url = f"https://rfen.es/especialidades/waterpolo/competicion/1510/resultados/4963/clasificacion/"
    print(f"📥 Descarregant classificació: {url}")
    
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    clasificacion = []
    
    # Buscar la taula de classificació
    rows = soup.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 9:
            try:
                team_name_elem = cells[1].find('a')
                team_name = team_name_elem.get_text(strip=True) if team_name_elem else cells[1].get_text(strip=True)
                
                clasificacion.append({
                    'position': cells[0].get_text(strip=True),
                    'team': team_name,
                    'played': int(cells[2].get_text(strip=True) or 0),
                    'won': int(cells[3].get_text(strip=True) or 0),
                    'drawn': int(cells[4].get_text(strip=True) or 0),
                    'lost': int(cells[5].get_text(strip=True) or 0),
                    'goals_for': int(cells[6].get_text(strip=True) or 0),
                    'goals_against': int(cells[7].get_text(strip=True) or 0),
                    'points': int(cells[8].get_text(strip=True) or 0)
                })
            except Exception as e:
                print(f"⚠️ Error parsejant fila: {e}")
    
    return clasificacion
    
def main():
    print("🏊 Parser RFEN per CN Caballa v1.2")
    print("=" * 50)
    
    # Últims partits
    ultimos = parse_partidos(f"{BASE_URL}/{TEAM_ID}/ultimos-partidos/")
    clasificacion = parse_clasificacion()
    
    # Pròxims partits
    proximos = parse_partidos(f"{BASE_URL}/{TEAM_ID}/proximos-partidos/")
    
    print(f"\n✅ Últims partits: {len(ultimos)}")
    print(f"✅ Pròxims partits: {len(proximos)}")
    
    # Mostrar resum
    print("\n📊 ÚLTIMS PARTITS:")
    for m in ultimos[:5]:
        local = m['local']
        away = m['away']
        result = f"{local['score']}-{away['score']}" if local['score'] is not None else "vs"
        home_marker = "🏠" if m['is_home'] else "✈️"
        print(f"   {home_marker} J{m['jornada']}: {local['name']} {result} {away['name']}")
    
    print("\n📅 PRÒXIMS PARTITS:")
    for m in proximos[:5]:
        local = m['local']
        away = m['away']
        home_marker = "🏠" if m['is_home'] else "✈️"
        print(f"   {home_marker} J{m['jornada']}: {local['name']} vs {away['name']} - {m['date']}")
    
    # Generar JSON
    output = {
        "team": TEAM_NAME,
        "team_id": TEAM_ID,
        "last_updated": datetime.now().isoformat(),
        "ultimos_partidos": ultimos,
        "proximos_partidos": proximos,
        "clasificacion": clasificacion,
        "locations": POOL_LOCATIONS
    }
    
    # Guardar
    with open('rfen_caballa_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Guardat a rfen_caballa_data.json")

if __name__ == "__main__":
    main()
