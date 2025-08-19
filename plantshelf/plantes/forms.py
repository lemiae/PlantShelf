# forms.py
from django import forms
from .models import Piece, EspecePlante, PlantePossedee


class PieceForm(forms.ModelForm):
    class Meta:
        model = Piece
        fields = ['nom', 'exposition', 'description', 'nombre_etageres']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salon, Chambre, Bureau...'
            }),
            'exposition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description optionnelle de la pièce...'
            }),
            'nombre_etageres': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'value': 3
            })
        }
        labels = {
            'nom': 'Nom de la pièce',
            'exposition': 'Exposition principale',
            'description': 'Description (optionnelle)',
            'nombre_etageres': 'Nombre d\'étagères'
        }
        help_texts = {
            'exposition': 'Quelle est l\'orientation principale de cette pièce ?',
            'nombre_etageres': 'Combien d\'étagères voulez-vous dans votre bibliothèque ? (1-10)'
        }

    def clean_nom(self):
        """Validation personnalisée du nom"""
        nom = self.cleaned_data.get('nom')
        if nom:
            nom = nom.strip().title()  # Nettoie et met en forme
            if len(nom) < 2:
                raise forms.ValidationError('Le nom doit faire au moins 2 caractères.')
        return nom


class EspecePlanteForm(forms.ModelForm):
    class Meta:
        model = EspecePlante
        fields = ['nom_commun', 'nom_scientifique', 'frequence_arrosage_jours', 'exposition_preferee']
        widgets = {
            'nom_commun': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ficus, Monstera, Pothos...'
            }),
            'nom_scientifique': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Ficus benjamina (optionnel)'
            }),
            'frequence_arrosage_jours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365,
                'value': 7
            }),
            'exposition_preferee': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'nom_commun': 'Nom commun',
            'nom_scientifique': 'Nom scientifique (optionnel)',
            'frequence_arrosage_jours': 'Fréquence d\'arrosage (en jours)',
            'exposition_preferee': 'Exposition préférée'
        }


class PlantePossedeeForm(forms.ModelForm):
    class Meta:
        model = PlantePossedee
        fields = ['espece', 'piece', 'nom_personnalise', 'etagere_numero', 'position_x', 'notes']
        widgets = {
            'espece': forms.Select(attrs={
                'class': 'form-control'
            }),
            'piece': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nom_personnalise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Mon Ficus du salon (optionnel)'
            }),
            'etagere_numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'position_x': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes personnelles sur cette plante...'
            })
        }
        labels = {
            'espece': 'Espèce de plante',
            'piece': 'Pièce',
            'nom_personnalise': 'Nom personnalisé (optionnel)',
            'etagere_numero': 'Numéro d\'étagère',
            'position_x': 'Position sur l\'étagère',
            'notes': 'Notes personnelles'
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les pièces pour cet utilisateur uniquement
        if user:
            self.fields['piece'].queryset = Piece.objects.filter(user=user)
        
        # Si une pièce est sélectionnée, limiter les étagères
        if 'piece' in self.data:
            try:
                piece_id = int(self.data.get('piece'))
                piece = Piece.objects.get(id=piece_id)
                self.fields['etagere_numero'].widget.attrs['max'] = piece.nombre_etageres
            except (ValueError, TypeError, Piece.DoesNotExist):
                pass
        elif self.instance.pk and self.instance.piece:
            self.fields['etagere_numero'].widget.attrs['max'] = self.instance.piece.nombre_etageres