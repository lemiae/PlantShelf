# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Piece, EspecePlante, PlantePossedee
from .forms import PieceForm


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
    """Vue bibliothèque d'une pièce spécifique"""
    piece = get_object_or_404(Piece, id=piece_id, user=request.user)
    plantes = PlantePossedee.objects.filter(piece=piece).select_related('espece')
    
    # Organiser les plantes par étagère
    plantes_par_etagere = {}
    for i in range(1, piece.nombre_etageres + 1):
        plantes_par_etagere[i] = plantes.filter(etagere_numero=i).order_by('position_x')
    
    context = {
        'piece': piece,
        'plantes_par_etagere': plantes_par_etagere,
        'total_plantes': plantes.count(),
        'plantes_a_arroser': [p for p in plantes if p.a_besoin_arrosage]
    }
    
    return render(request, 'plantes/bibliotheque_piece.html', context)