"""
Manejo de bases de datos: motos, pilotos, lugares.
Almacenamiento en archivos JSON.
"""
import json
import os
from config import DATA_DIR

MOTOS_FILE = os.path.join(DATA_DIR, 'motos.json')
PILOTOS_FILE = os.path.join(DATA_DIR, 'pilotos.json')
LUGARES_FILE = os.path.join(DATA_DIR, 'lugares.json')


class DataHandler:
    def __init__(self):
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Crea archivos JSON vacíos si no existen."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        for filepath in [MOTOS_FILE, PILOTOS_FILE, LUGARES_FILE]:
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    # ══════════════════════════════════════════════════
    # MOTOS
    # ══════════════════════════════════════════════════
    def load_motos(self):
        try:
            with open(MOTOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_motos(self, motos):
        with open(MOTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(motos, f, indent=4, ensure_ascii=False)

    def add_moto(self, moto_data):
        motos = self.load_motos()
        motos.append(moto_data)
        self.save_motos(motos)

    def update_moto(self, index, moto_data):
        motos = self.load_motos()
        if 0 <= index < len(motos):
            motos[index] = moto_data
            self.save_motos(motos)

    def delete_moto(self, index):
        motos = self.load_motos()
        if 0 <= index < len(motos):
            del motos[index]
            self.save_motos(motos)

    # ══════════════════════════════════════════════════
    # PILOTOS
    # ══════════════════════════════════════════════════
    def load_pilotos(self):
        try:
            with open(PILOTOS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Migración: si es lista de strings, convertir a dicts
            migrated = []
            modified = False
            for item in data:
                if isinstance(item, str):
                    migrated.append({"nombre": item, "peso": 0, "altura": 0})
                    modified = True
                else:
                    if "altura" not in item:
                        item["altura"] = 0
                        modified = True
                    migrated.append(item)

            if modified:
                self.save_pilotos(migrated)
            return migrated
        except Exception:
            return []

    def save_pilotos(self, pilotos):
        with open(PILOTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pilotos, f, indent=4, ensure_ascii=False)

    def add_piloto(self, nombre, peso=0, altura=0):
        pilotos = self.load_pilotos()
        if not any(p.get('nombre') == nombre for p in pilotos):
            pilotos.append({"nombre": nombre, "peso": peso, "altura": altura})
            self.save_pilotos(pilotos)

    def update_piloto(self, old_nombre, new_nombre, new_peso, new_altura):
        pilotos = self.load_pilotos()
        for p in pilotos:
            if p.get('nombre') == old_nombre:
                p['nombre'] = new_nombre
                p['peso'] = new_peso
                p['altura'] = new_altura
                break
        self.save_pilotos(pilotos)

    def delete_piloto(self, nombre):
        pilotos = self.load_pilotos()
        pilotos = [p for p in pilotos if p.get('nombre') != nombre]
        self.save_pilotos(pilotos)

    # ══════════════════════════════════════════════════
    # LUGARES
    # ══════════════════════════════════════════════════
    def load_lugares(self):
        try:
            with open(LUGARES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def save_lugares(self, lugares):
        with open(LUGARES_FILE, 'w', encoding='utf-8') as f:
            json.dump(lugares, f, indent=4, ensure_ascii=False)

    def add_lugar(self, lugar_data):
        lugares = self.load_lugares()
        lugares.append(lugar_data)
        self.save_lugares(lugares)

    def delete_lugar(self, index):
        lugares = self.load_lugares()
        if 0 <= index < len(lugares):
            del lugares[index]
            self.save_lugares(lugares)
