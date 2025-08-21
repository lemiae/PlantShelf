# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Piece, EspecePlante, PlantePossedee
from .forms import PieceForm
from django.views.decorators.http import require_http_methods
from .forms import AjouterPlanteForm, CreerEspeceForm
from .services.perenual_service import perenual_service
import json
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def home(request):
    """Page d'accueil - redirection selon authentification"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'plantes/home.html')


def register_view(request):
    """Inscription utilisateur"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            
            # Connexion automatique après inscription
            user = authenticate(username=username, password=form.cleaned_data.get('password1'))
            if user:
                login(request, user)
                return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard principal"""
    pieces = Piece.objects.filter(user=request.user)
    
    # Statistiques rapides
    total_plantes = PlantePossedee.objects.filter(user=request.user).count()
    plantes_a_arroser = [p for p in PlantePossedee.objects.filter(user=request.user) if p.a_besoin_arrosage]
    
    context = {
        'pieces': pieces,
        'total_plantes': total_plantes,
        'nombre_pieces': pieces.count(),
        'plantes_a_arroser': len(plantes_a_arroser),
        'notifications_urgentes': plantes_a_arroser[:5]  # Les 5 plus urgentes
    }
    
    return render(request, 'plantes/dashboard.html', context)


@login_required
def mes_pieces(request):
    """Liste des pièces de l'utilisateur"""
    pieces = Piece.objects.filter(user=request.user)
    
    # Enrichir chaque pièce avec ses stats
    pieces_avec_stats = []
    for piece in pieces:
        plantes = PlantePossedee.objects.filter(piece=piece)
        pieces_avec_stats.append({
            'piece': piece,
            'nombre_plantes': plantes.count(),
            'plantes_a_arroser': len([p for p in plantes if p.a_besoin_arrosage])
        })
    
    context = {
        'pieces_avec_stats': pieces_avec_stats
    }
    
    return render(request, 'plantes/mes_pieces.html', context)


@login_required
def creer_piece(request):
    """Créer une nouvelle pièce"""
    if request.method == 'POST':
        form = PieceForm(request.POST)
        if form.is_valid():
            piece = form.save(commit=False)
            piece.user = request.user
            piece.save()
            messages.success(request, f'Pièce "{piece.nom}" créée avec succès!')
            return redirect('mes_pieces')
    else:
        form = PieceForm()
    
    return render(request, 'plantes/creer_piece.html', {'form': form})


@login_required
def modifier_piece(request, piece_id):
    """Modifier une pièce existante"""
    piece = get_object_or_404(Piece, id=piece_id, user=request.user)
    
    if request.method == 'POST':
        form = PieceForm(request.POST, instance=piece)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pièce "{piece.nom}" modifiée avec succès!')
            return redirect('mes_pieces')
    else:
        form = PieceForm(instance=piece)
    
    return render(request, 'plantes/modifier_piece.html', {'form': form, 'piece': piece})


@login_required
def supprimer_piece(request, piece_id):
    """Supprimer une pièce"""
    piece = get_object_or_404(Piece, id=piece_id, user=request.user)
    
    if request.method == 'POST':
        nom_piece = piece.nom
        piece.delete()
        messages.success(request, f'Pièce "{nom_piece}" supprimée avec succès!')
        return redirect('mes_pieces')
    
    return render(request, 'plantes/supprimer_piece.html', {'piece': piece})


@login_required
def bibliotheque_piece(request, piece_id):
    """Affiche la bibliothèque d'une pièce avec ses plantes sur les étagères"""
    piece = get_object_or_404(Piece, id=piece_id, user=request.user)
    
    # Récupérer toutes les plantes de la pièce, triées par étagère et position
    plantes = PlantePossedee.objects.filter(piece=piece).select_related('espece').order_by('etagere_numero', 'position_x')
    
    # Créer une liste des numéros d'étagères pour le template
    etageres_range = list(range(1, piece.nombre_etageres + 1))
    
    # Identifier les plantes qui ont besoin d'arrosage
    plantes_a_arroser = [plante for plante in plantes if plante.a_besoin_arrosage]
    
    # Statistiques rapides
    context = {
        'piece': piece,
        'plantes': plantes,
        'etageres_range': etageres_range,
        'plantes_a_arroser': plantes_a_arroser,
        'total_plantes': len(plantes),
        'nb_etageres': piece.nombre_etageres,
    }
    
    return render(request, 'plantes/bibliotheque_piece.html', context)

@login_required
@require_http_methods(["GET"])
def api_rechercher_plantes(request):
    """API endpoint pour l'autocomplete de recherche de plantes"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Chercher d'abord dans notre base locale
    especes_locales = EspecePlante.objects.filter(
        nom_commun__icontains=query
    )[:5]
    
    results = []
    
    # Ajouter les espèces locales
    for espece in especes_locales:
        results.append({
            'id': f'local_{espece.id}',
            'text': espece.nom_commun,
            'scientific_name': espece.nom_scientifique or '',
            'source': 'local',
            'frequence_arrosage': espece.frequence_arrosage_jours,
            'exposition': espece.get_exposition_preferee_display()
        })
    
    # Chercher dans l'API Perenual si on n'a pas assez de résultats
    if len(results) < 10:
        try:
            api_results = perenual_service.search_plants(query, limit=10)
            
            for plant in api_results:
                if len(results) >= 15:  # Limite totale
                    break
                    
                results.append({
                    'id': f'api_{plant["id"]}',
                    'text': plant.get('common_name', ''),
                    'scientific_name': plant.get('scientific_name', [None])[0] if plant.get('scientific_name') else '',
                    'source': 'api',
                    'image': plant.get('default_image', {}).get('thumbnail') if plant.get('default_image') else None
                })
        except Exception as e:
            # En cas d'erreur API, continuer avec les résultats locaux
            pass
    
    return JsonResponse({'results': results})


@login_required
def ajouter_plante(request, piece_id=None):
    """Vue pour ajouter une plante à une pièce"""
    piece = None
    if piece_id:
        piece = get_object_or_404(Piece, id=piece_id, user=request.user)
    
    if request.method == 'POST':
        form = AjouterPlanteForm(request.user, request.POST)
        
        if form.is_valid():
            # Récupérer ou créer l'espèce
            espece = None
            recherche_espece = request.POST.get('recherche_espece', '').strip()
            espece_selectionnee = request.POST.get('espece_selectionnee', '').strip()
            
            if espece_selectionnee:
                # Traiter la sélection d'espèce
                if espece_selectionnee.startswith('local_'):
                    # Espèce existante dans notre base
                    espece_id = int(espece_selectionnee.replace('local_', ''))
                    espece = get_object_or_404(EspecePlante, id=espece_id)
                    
                elif espece_selectionnee.startswith('api_'):
                    # Nouvelle espèce depuis l'API Perenual
                    perenual_id = int(espece_selectionnee.replace('api_', ''))
                    
                    # Vérifier si on l'a déjà en base
                    espece = EspecePlante.objects.filter(perenual_id=perenual_id).first()
                    
                    if not espece:
                        # Créer la nouvelle espèce depuis l'API
                        try:
                            # D'abord essayer d'obtenir les détails complets
                            plant_data = perenual_service.get_plant_details(perenual_id)
                            if plant_data:
                                espece_data = perenual_service.format_plant_for_model(plant_data)
                                if espece_data:
                                    espece = EspecePlante.objects.create(**espece_data)
                                    messages.success(request, f"Nouvelle espèce '{espece.nom_commun}' créée depuis l'API Perenual.")
                            else:
                                raise Exception("Données non disponibles")
                                
                        except Exception as e:
                            # Fallback : créer avec des données minimales depuis la recherche
                            try:
                                # Récupérer le nom depuis le formulaire
                                nom_recherche = request.POST.get('nom_plante_cache') or request.POST.get('recherche_espece', '').strip()
                                if nom_recherche:
                                    espece_data = {
                                        'nom_commun': nom_recherche.title(),
                                        'perenual_id': perenual_id,
                                        'frequence_arrosage_jours': 7,
                                        'exposition_preferee': 'indirecte',
                                    }
                                    espece = EspecePlante.objects.create(**espece_data)
                                    messages.warning(request, f"Espèce '{espece.nom_commun}' créée avec des paramètres par défaut (limite API atteinte).")
                                else:
                                    raise Exception("Nom de plante non trouvé")
                            except Exception as e2:
                                messages.error(request, f"Impossible de créer l'espèce. Erreur: {e2}")
                                return render(request, 'plantes/ajouter_plante.html', {
                                    'form': form, 
                                    'piece': piece
                                })
            
            if not espece:
                messages.error(request, "Veuillez sélectionner une espèce valide.")
                return render(request, 'plantes/ajouter_plante.html', {
                    'form': form, 
                    'piece': piece
                })
            
            # Créer la plante possédée
            plante = form.save(commit=False)
            plante.user = request.user
            plante.espece = espece
            plante.save()
            
            messages.success(request, f"Plante '{plante.nom_affiche}' ajoutée avec succès!")
            return redirect('bibliotheque_piece', piece_id=plante.piece.id)
    
    else:
        initial_data = {}
        if piece:
            initial_data['piece'] = piece.id  # Passer l'ID, pas l'objet
        form = AjouterPlanteForm(request.user, initial=initial_data)
    
    return render(request, 'plantes/ajouter_plante.html', {
        'form': form,
        'piece': piece
    })


@login_required
def creer_espece_manuelle(request):
    """Vue pour créer une espèce manuellement"""
    if request.method == 'POST':
        form = CreerEspeceForm(request.POST)
        if form.is_valid():
            espece = form.save()
            messages.success(request, f"Espèce '{espece.nom_commun}' créée avec succès!")
            return redirect('ajouter_plante')
    else:
        form = CreerEspeceForm()
    
    return render(request, 'plantes/creer_espece.html', {'form': form})

@login_required
@require_POST
def arroser_plante(request, plante_id):
    """Marque une plante comme arrosée (AJAX)"""
    plante = get_object_or_404(PlantePossedee, id=plante_id, user=request.user)
    
    # Mettre à jour la date d'arrosage
    plante.derniere_fois_arrosee = timezone.now()
    plante.save()
    
    return JsonResponse({
        'success': True,
        'message': f'{plante.nom_affiche} a été arrosée !',
        'derniere_fois_arrosee': plante.derniere_fois_arrosee.isoformat(),
        'jours_depuis_arrosage': plante.jours_depuis_arrosage
    })


@login_required
@require_POST
def deplacer_plante(request, plante_id):
    """Déplace une plante à une nouvelle position (AJAX)"""
    try:
        plante = get_object_or_404(PlantePossedee, id=plante_id, user=request.user)
        
        # Récupérer les données JSON
        data = json.loads(request.body)
        nouvelle_etagere = data.get('etagere_numero')
        nouvelle_position = data.get('position_x')
        
        # Validation
        if not (1 <= nouvelle_etagere <= plante.piece.nombre_etageres):
            return JsonResponse({
                'success': False,
                'error': 'Numéro d\'étagère invalide'
            })
        
        if nouvelle_position < 0:
            nouvelle_position = 0
        
        # Sauvegarder
        plante.etagere_numero = nouvelle_etagere
        plante.position_x = nouvelle_position
        plante.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{plante.nom_affiche} déplacée vers l\'étagère {nouvelle_etagere}',
            'nouvelle_etagere': nouvelle_etagere,
            'nouvelle_position': nouvelle_position
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })