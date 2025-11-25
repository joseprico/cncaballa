#!/usr/bin/env python3
"""
Puja les dades RFEN a Firebase Realtime Database
Versió 1.1 - Amb classificació
"""

import firebase_admin
from firebase_admin import credentials, db
import json
import os
from datetime import datetime
import re

def normalize_key(key):
    """Normalitza una clau per Firebase (sense . $ # [ ] /)"""
    # Eliminar caràcters no permesos
    normalized = re.sub(r'[.$#\[\]/]', '_', key)
    # Eliminar espais múltiples i guions baixos consecutius
    normalized = re.sub(r'[_\s]+', '_', normalized)
    # Eliminar guions baixos al principi i final
    normalized = normalized.strip('_')
    return normalized

def normalize_data(data):
    """Normalitza recursivament totes les claus d'un diccionari"""
    if isinstance(data, dict):
        return {normalize_key(k): normalize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [normalize_data(item) for item in data]
    else:
        return data

def main():
    print("🔥 Pujant dades RFEN a Firebase...")
    
    # Obtenir credencials del secret de GitHub Actions
    cred_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    
    if not cred_json:
        print("❌ Error: No s'ha trobat FIREBASE_SERVICE_ACCOUNT")
        print("   Assegura't de configurar el secret a GitHub")
        exit(1)
    
    try:
        # Inicialitzar Firebase
        cred = credentials.Certificate(json.loads(cred_json))
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://cn-caballa-wpstats-default-rtdb.europe-west1.firebasedatabase.app'
        })
        print("✅ Firebase inicialitzat")
        
    except Exception as e:
        print(f"❌ Error inicialitzant Firebase: {e}")
        exit(1)
    
    # Llegir dades del JSON
    try:
        with open('rfen_caballa_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ultimos_count = len(data.get('ultimos_partidos', []))
        proximos_count = len(data.get('proximos_partidos', []))
        clasificacion_count = len(data.get('clasificacion', []))
        
        print(f"✅ Llegides dades:")
        print(f"   • {ultimos_count} últims partits")
        print(f"   • {proximos_count} pròxims partits")
        print(f"   • {clasificacion_count} equips a la classificació")
        
    except FileNotFoundError:
        print("❌ Error: No s'ha trobat rfen_caballa_data.json")
        print("   Executa primer rfen_parser.py")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error llegint JSON: {e}")
        exit(1)
    
    # Normalitzar les dades per Firebase
    print("🔧 Normalitzant claus per Firebase...")
    data_normalized = normalize_data(data)
    
    # Pujar a Firebase
    try:
        ref = db.reference('rfen_data')
        ref.set(data_normalized)
        print("✅ Dades pujades a Firebase correctament!")
        
        # Actualitzar timestamp de l'última sincronització
        sync_ref = db.reference('rfen_sync')
        sync_ref.set({
            'last_sync': datetime.now().isoformat(),
            'ultimos_count': ultimos_count,
            'proximos_count': proximos_count,
            'clasificacion_count': clasificacion_count
        })
        print("✅ Timestamp actualitzat")
        
        # Mostrar resum de la classificació
        if clasificacion_count > 0:
            clasificacion = data.get('clasificacion', [])
            caballa = next((t for t in clasificacion if 'caballa' in t.get('team', '').lower() or 'ceuta' in t.get('team', '').lower()), None)
            if caballa:
                print(f"\n🏆 CN Caballa:")
                print(f"   Posició: {caballa['position']}ª")
                print(f"   Punts: {caballa['points']}")
                print(f"   {caballa['won']}V - {caballa['lost']}D")
                print(f"   GF: {caballa['goals_for']} - GC: {caballa['goals_against']}")
        
    except Exception as e:
        print(f"❌ Error pujant a Firebase: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n🎉 Sincronització completada!")

if __name__ == "__main__":
    main()
