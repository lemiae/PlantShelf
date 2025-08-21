# urls.py (dans ton app)
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),
    
    # Authentification
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestion des pièces
    path('pieces/', views.mes_pieces, name='mes_pieces'),
    path('pieces/creer/', views.creer_piece, name='creer_piece'),
    path('pieces/<int:piece_id>/modifier/', views.modifier_piece, name='modifier_piece'),
    path('pieces/<int:piece_id>/supprimer/', views.supprimer_piece, name='supprimer_piece'),
    
    # Bibliothèque par pièce
    path('pieces/<int:piece_id>/bibliotheque/', views.bibliotheque_piece, name='bibliotheque_piece'),

    # Gestion des plantes
    path('plantes/', views.creer_espece_manuelle, name='creer_espece'),
    #path('plantes/ajouter/', views.ajouter_plante, name='ajouter_plantes'),
    path('ajouter-plante/', views.ajouter_plante, name='ajouter_plante'),
    path('ajouter-plante/<int:piece_id>/', views.ajouter_plante, name='ajouter_plante'),
    path('api/rechercher-plantes/', views.api_rechercher_plantes, name='api_rechercher_plantes'),
    path('creer-espece/', views.creer_espece_manuelle, name='creer_espece_manuelle'),
    path('plante/<int:plante_id>/arroser/', views.arroser_plante, name='arroser_plante'),
    path('plante/<int:plante_id>/deplacer/', views.deplacer_plante, name='deplacer_plante'),


]
