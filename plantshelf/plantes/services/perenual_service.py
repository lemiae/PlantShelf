# services/perenual_service.py
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class PerenualService:
    BASE_URL = "https://perenual.com/api"
    
    def __init__(self):
        self.api_key = settings.PERENUAL_API_KEY
        self.session = requests.Session()
    
    def search_plants(self, query, limit=20):
        """Recherche de plantes par nom"""
        cache_key = f"perenual_search_{query}_{limit}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            url = f"{self.BASE_URL}/species-list"
            params = {
                'key': self.api_key,
                'q': query,
                'page': 1,
                'per_page': limit,
                'indoor': 1  # Seulement les plantes d'intérieur
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            result = data.get('data', [])
            
            # Cache pour 1 heure
            cache.set(cache_key, result, 3600)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Perenual search: {e}")
            return []
    
    def get_plant_details(self, plant_id):
        """Récupère les détails d'une plante par son ID"""
        cache_key = f"perenual_plant_{plant_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            url = f"{self.BASE_URL}/species/details/{plant_id}"
            params = {'key': self.api_key}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache pour 24 heures (les détails changent rarement)
            cache.set(cache_key, result, 86400)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Perenual details: {e}")
            return None
    
    def get_care_guides(self, plant_id):
        """Récupère les guides d'entretien"""
        cache_key = f"perenual_care_{plant_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            url = f"{self.BASE_URL}/species-care-guide-list"
            params = {
                'key': self.api_key,
                'species_id': plant_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # Cache pour 24 heures
            cache.set(cache_key, result, 86400)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Perenual care: {e}")
            return None
    
    def format_plant_for_model(self, plant_data):
        """Convertit les données API vers le format de notre modèle"""
        if not plant_data:
            return None
        
        # Mapping des types de lumière Perenual vers nos choix
        sunlight_mapping = {
            'full_sun': 'directe',
            'part_sun': 'indirecte', 
            'part_shade': 'indirecte',
            'full_shade': 'faible'
        }
        
        sunlight = plant_data.get('sunlight', [])
        if sunlight and isinstance(sunlight, list):
            perenual_light = sunlight[0].lower().replace(' ', '_').replace('-', '_')
            exposition = sunlight_mapping.get(perenual_light, 'indirecte')
        else:
            exposition = 'indirecte'
        
        # Estimation de la fréquence d'arrosage basée sur le type de plante
        watering = plant_data.get('watering', '').lower()
        if 'frequent' in watering or 'daily' in watering:
            frequence = 3
        elif 'average' in watering or 'regular' in watering:
            frequence = 7
        elif 'minimum' in watering or 'rare' in watering:
            frequence = 14
        else:
            frequence = 7  # Défaut
        
        return {
            'nom_commun': plant_data.get('common_name', '').title(),
            'nom_scientifique': plant_data.get('scientific_name', [None])[0] if plant_data.get('scientific_name') else None,
            'perenual_id': plant_data.get('id'),
            'frequence_arrosage_jours': frequence,
            'exposition_preferee': exposition,
        }

# Instance globale du service
perenual_service = PerenualService()