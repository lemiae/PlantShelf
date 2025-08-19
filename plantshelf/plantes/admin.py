# admin.py
from django.contrib import admin
from .models import Piece, EspecePlante, PlantePossedee


@admin.register(Piece)
class PieceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'user', 'exposition', 'nombre_etageres', 'nombre_plantes', 'created_at')
    list_filter = ('exposition', 'nombre_etageres', 'created_at')
    search_fields = ('nom', 'user__username', 'description')
    ordering = ('user', 'nom')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'nom', 'exposition', 'description')
        }),
        ('Configuration', {
            'fields': ('nombre_etageres',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(EspecePlante)
class EspecePlanteAdmin(admin.ModelAdmin):
    list_display = ('nom_commun', 'nom_scientifique', 'frequence_arrosage_jours', 'exposition_preferee', 'perenual_id')
    list_filter = ('exposition_preferee', 'frequence_arrosage_jours')
    search_fields = ('nom_commun', 'nom_scientifique')
    ordering = ('nom_commun',)
    
    fieldsets = (
        ('Identification', {
            'fields': ('nom_commun', 'nom_scientifique', 'perenual_id')
        }),
        ('Caractéristiques', {
            'fields': ('frequence_arrosage_jours', 'exposition_preferee')
        }),
        ('Design (Phase 4)', {
            'fields': ('image_design', 'couleur_pot'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlantePossedee)
class PlantePossedeeAdmin(admin.ModelAdmin):
    list_display = ('nom_affiche_admin', 'user', 'espece', 'piece', 'etagere_numero', 'jours_depuis_arrosage', 'a_besoin_arrosage')
    list_filter = ('piece__exposition', 'espece__exposition_preferee', 'etagere_numero', 'created_at')
    search_fields = ('nom_personnalise', 'espece__nom_commun', 'piece__nom', 'user__username')
    ordering = ('user', 'piece', 'etagere_numero', 'position_x')
    
    fieldsets = (
        ('Identification', {
            'fields': ('user', 'espece', 'nom_personnalise')
        }),
        ('Localisation', {
            'fields': ('piece', 'etagere_numero', 'position_x')
        }),
        ('Entretien', {
            'fields': ('derniere_fois_arrosee',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def nom_affiche_admin(self, obj):
        return obj.nom_affiche
    nom_affiche_admin.short_description = 'Nom'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'espece', 'piece')
    
    # Actions personnalisées
    actions = ['marquer_arrose']
    
    def marquer_arrose(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(derniere_fois_arrosee=timezone.now())
        self.message_user(request, f'{updated} plante(s) marquée(s) comme arrosée(s).')
    marquer_arrose.short_description = "Marquer comme arrosé(s)"


# Configuration du site admin
admin.site.site_header = "Administration PlantApp"
admin.site.site_title = "PlantApp Admin"
admin.site.index_title = "Gestion de l'application"