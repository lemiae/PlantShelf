# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Piece(models.Model):
    EXPOSITION_CHOICES = [
        ('nord', 'Nord'),
        ('sud', 'Sud'),
        ('est', 'Est'),
        ('ouest', 'Ouest'),
        ('nord_est', 'Nord-Est'),
        ('nord_ouest', 'Nord-Ouest'),
        ('sud_est', 'Sud-Est'),
        ('sud_ouest', 'Sud-Ouest'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pieces')
    nom = models.CharField(max_length=100)
    exposition = models.CharField(max_length=20, choices=EXPOSITION_CHOICES)
    description = models.TextField(blank=True, null=True)
    nombre_etageres = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nom']
        unique_together = ['user', 'nom']  # Pas deux pièces avec le même nom pour un user
    
    def __str__(self):
        return f"{self.nom} ({self.exposition})"
    
    @property
    def nombre_plantes(self):
        return self.plantes.count()


class EspecePlante(models.Model):
    EXPOSITION_CHOICES = [
        ('faible', 'Lumière faible'),
        ('indirecte', 'Lumière indirecte'),
        ('directe', 'Lumière directe'),
        ('variable', 'Variable'),
    ]
    
    nom_commun = models.CharField(max_length=100)
    nom_scientifique = models.CharField(max_length=100, blank=True, null=True)
    
    # Données de l'API Perenual (optionnel pour commencer)
    perenual_id = models.IntegerField(blank=True, null=True, unique=True)
    
    # Caractéristiques d'entretien
    frequence_arrosage_jours = models.IntegerField(default=7, validators=[MinValueValidator(1), MaxValueValidator(365)])
    exposition_preferee = models.CharField(max_length=20, choices=EXPOSITION_CHOICES, default='indirecte')
    
    # Design personnalisé (à implémenter plus tard)
    image_design = models.ImageField(upload_to='plantes_designs/', blank=True, null=True)
    couleur_pot = models.CharField(max_length=7, default="#8B4513")  # Couleur hex
    
    # Meta données
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom_commun']
    
    def __str__(self):
        return self.nom_commun


class PlantePossedee(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plantes')
    espece = models.ForeignKey(EspecePlante, on_delete=models.CASCADE, related_name='instances')
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE, related_name='plantes')
    
    # Nom personnalisé de la plante (ex: "Mon Ficus", "Plante du salon")
    nom_personnalise = models.CharField(max_length=100, blank=True, null=True)
    
    # Position dans la bibliothèque
    etagere_numero = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    position_x = models.IntegerField(default=0)  # Position horizontale sur l'étagère
    
    # Suivi d'arrosage
    derniere_fois_arrosee = models.DateTimeField(auto_now_add=True)
    
    # Notes personnelles
    notes = models.TextField(blank=True, null=True)
    
    # Meta données
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['piece', 'etagere_numero', 'position_x']
    
    def __str__(self):
        nom = self.nom_personnalise or self.espece.nom_commun
        return f"{nom} - {self.piece.nom}"
    
    @property
    def nom_affiche(self):
        return self.nom_personnalise or self.espece.nom_commun
    
    @property
    def jours_depuis_arrosage(self):
        from django.utils import timezone
        return (timezone.now() - self.derniere_fois_arrosee).days
    
    @property
    def a_besoin_arrosage(self):
        return self.jours_depuis_arrosage >= self.espece.frequence_arrosage_jours