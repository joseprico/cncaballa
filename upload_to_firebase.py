#!/usr/bin/env python3
"""
Puja les dades RFEN a Firebase Realtime Database
"""

import firebase_admin
from firebase_admin import credentials, db
import json
import os
from datetime import datetime

def main():
    print("🔥 Pujant dades a Firebase...")
    
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
        print(f"✅ Llegides dades: {len(data.get('ultimos_partidos', []))} últims, {len(data.get('proximos_partidos', []))} pròxims")
        
    except FileNotFoundError:
        print("❌ Error: No s'ha trobat rfen_caballa_data.json")
        print("   Executa primer rfen_parser.py")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error llegint JSON: {e}")
        exit(1)
    
    # Pujar a Firebase
    try:
        ref = db.reference('rfen_data')
        ref.set(data)
        print("✅ Dades pujades a Firebase correctament!")
        
        # Actualitzar timestamp de l'última sincronització
        sync_ref = db.reference('rfen_sync')
        sync_ref.set({
            'last_sync': datetime.now().isoformat(),
            'ultimos_count': len(data.get('ultimos_partidos', [])),
            'proximos_count': len(data.get('proximos_partidos', []))
        })
        print("✅ Timestamp actualitzat")
        
    except Exception as e:
        print(f"❌ Error pujant a Firebase: {e}")
        exit(1)
    
    print("\n🎉 Sincronització completada!")

if __name__ == "__main__":
    main()
