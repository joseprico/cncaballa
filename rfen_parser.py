#!/usr/bin/env python3
"""
Parser RFEN per CN Caballa
Extreu partits passats, futurs i classificació de la RFEN
Versió 1.3 - Amb classificació
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
GRUPO_ID = "2485"  # Grupo de la lliga
BASE_URL = "https://rfen.es/especialidades/waterpolo/equipo"
CLASIFICACION_URL = "https://rfen.es/especialidades/waterpolo/grupo"

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
    url = "https://rfen.es/especialidades/waterpolo/competicion/1510/resultados/4963/clasificacion/"
    print(f"📥 Descarregant classificació: {url}")
    
    try:
        html = fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        clasificacion = []
        
        # Buscar el contenidor de la taula
        table_body = soup.find('div', class_='RFEN_TableBody')
        if not table_body:
            print("⚠️ No s'ha trobat RFEN_TableBody")
            return []
        
        # Buscar totes les files
        rows = table_body.find_all('div', class_='RFEN_TableBodyRow')
        print(f"   Trobades {len(rows)} files")
        
        for row in rows:
            try:
                # Buscar totes les columnes
                columns = row.find_all('div', class_='RFEN_TableBodyColumn')
                
                # Posició (primer div amb id)
                position_elem = row.find('div', id='RFEN_TableColumn_clasificationPosition')
                position = position_elem.get_text(strip=True) if position_elem else ""
                
                # Nom de l'equip (dins de l'enllaç)
                name_link = row.find('a')
                if name_link:
                    name_elem = name_link.find('div', id='RFEN_TableColumn_clasificationName')
                    team_name = name_elem.get_text(strip=True) if name_elem else ""
                    team_url = name_link.get('href', '')
                else:
                    team_name = ""
                    team_url = ""
                
                # Logo (buscar img dins de l'enllaç o a la fila)
                img = row.find('img')
                team_logo = img.get('src') if img else ""
                
                # Les dades estan als divs amb classe RFEN_TableColumn_clasificationMeta
                meta_columns = row.find_all('div', class_='RFEN_TableColumn_clasificationMeta')
                
                if len(meta_columns) >= 9:
                    clasificacion.append({
                        'position': position,
                        'team': team_name,
                        'logo': team_logo,
                        'team_url': team_url,
                        'points': int(meta_columns[0].get_text(strip=True) or 0),      # P
                        'played': int(meta_columns[1].get_text(strip=True) or 0),      # PJ
                        'won': int(meta_columns[2].get_text(strip=True) or 0),         # PG
                        'lost': int(meta_columns[3].get_text(strip=True) or 0),        # PP
                        'won_penalties': int(meta_columns[4].get_text(strip=True) or 0),  # PGP
                        'lost_penalties': int(meta_columns[5].get_text(strip=True) or 0), # PPP
                        'goals_for': int(meta_columns[6].get_text(strip=True) or 0),   # GF
                        'goals_against': int(meta_columns[7].get_text(strip=True) or 0), # GC
                        'goal_diff': int(meta_columns[8].get_text(strip=True) or 0)    # DG
                    })
                    
            except Exception as e:
                print(f"⚠️ Error parsejant fila classificació: {e}")
        
        print(f"✅ Classificació: {len(clasificacion)} equips")
        return clasificacion
        
    except Exception as e:
        print(f"❌ Error obtenint classificació: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("🏊 Parser RFEN per CN Caballa v1.3")
    print("=" * 50)
    
    # Últims partits
    ultimos = parse_partidos(f"{BASE_URL}/{TEAM_ID}/ultimos-partidos/")
    
    # Pròxims partits
    proximos = parse_partidos(f"{BASE_URL}/{TEAM_ID}/proximos-partidos/")
    
    # Classificació
    clasificacion = parse_clasificacion()
    
    print(f"\n✅ Últims partits: {len(ultimos)}")
    print(f"✅ Pròxims partits: {len(proximos)}")
    print(f"✅ Equips classificació: {len(clasificacion)}")
    
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
    
    # Mostrar posició a la classificació
    caballa = next((t for t in clasificacion if 'caballa' in t['team'].lower() or 'ceuta' in t['team'].lower()), None)
    if caballa:
        print(f"\n🏆 CLASSIFICACIÓ:")
        print(f"   Posició: {caballa['position']}ª")
        print(f"   Punts: {caballa['points']}")
        print(f"   {caballa['won']}V - {caballa['drawn']}E - {caballa['lost']}D")
    
    # Generar JSON
    output = {
        "team": TEAM_NAME,
        "team_id": TEAM_ID,
        "grupo_id": GRUPO_ID,
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
