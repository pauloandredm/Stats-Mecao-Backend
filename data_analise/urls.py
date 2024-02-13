"""
URL configuration for data_analise project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from analise.api import viewsets as analiseviewsets
from analise.api import serializers

route = routers.DefaultRouter()
route.register('register', analiseviewsets.RegisterViewSet)
route.register(r'Jogador', analiseviewsets.JogadorViewSet, basename="jogador")
route.register(r'Campeonato', analiseviewsets.CampeonatoViewSet, basename="campeonato")
route.register(r'Time', analiseviewsets.TimeViewSet, basename="Time")
route.register(r'Confronto', analiseviewsets.ConfrontoCreateViewSet, basename="Confronto")
route.register(r'ConfrontoView', analiseviewsets.ConfrontoViewSet, basename="ConfrontoView")
route.register(r'Escalacao', analiseviewsets.EscalacaoViewSet, basename="Escalacao")
route.register(r'EscalacaoCreate', analiseviewsets.EscalacaoCreateViewSet, basename="EscalacaoCreate")
route.register(r'Substituicao', analiseviewsets.SubstituicaoViewSet, basename="Substituicao")
route.register(r'lances', analiseviewsets.LanceViewSet)
route.register(r'confrontos', analiseviewsets.ConfrontoPlacarViewSet)
route.register(r'tiposLances', analiseviewsets.TiposLancesViewSet, basename='tiposLances')
route.register(r'lancesFiltro', analiseviewsets.LanceFilterViewSet)
route.register(r'confrontos/acrescimos',  analiseviewsets.ConfrontoAcrescimosViewSet, basename='confronto-acrescimos')
route.register(r'lancescoordenada', analiseviewsets.LanceCoordenadaViewSet, basename='lancecoordenada')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(route.urls)),
    path('token/', TokenObtainPairView.as_view(serializer_class=serializers.CustomTokenObtainPairSerializer)),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('escalacao/confronto/<int:confronto_id>/', analiseviewsets.EscalacaoConfrontoView.as_view(), name='escalacao_confronto'),
    path('em_campo/confronto/<int:confronto_id>/', analiseviewsets.EscalacaoConfrontoSemAdversarioView.as_view(), name='em_campo_confronto'),
    path('reservas/confronto/<int:confronto_id>/', analiseviewsets.JogadoresForaEscalacaoView.as_view(), name='reservas_confronto'),
    path('substituicao/confronto/<int:confronto_id>/', analiseviewsets.SubstituicaoConfrontoViewSet.as_view(), name='substituicao_confronto'),
    path('escalacaoedit/confronto/<int:confronto_id>/', analiseviewsets.EscalacaoEditView.as_view(), name='escalacao_edit'),
    path('jogadores-nao-titulares/', analiseviewsets.JogadoresNaoTitularViewSet.as_view({'get': 'list'}), name='jogadores-nao-titulares'),
    path('remover_jogador/<int:confronto_id>/<int:jogador_id>/', analiseviewsets.remover_jogador, name='remover_jogador'),
    path('adicionar_jogador/<int:confronto_id>/<int:jogador_id>/', analiseviewsets.adicionar_jogador, name='adicionar_jogador'),
    path('jogadores_disponiveis/<int:confronto_id>/', analiseviewsets.jogadores_disponiveis, name='jogadores_disponiveis'),
    path('confronto/<int:confronto_id>/jogadores/', analiseviewsets.jogadores_no_confronto),
    path('estatisticas-jogadores/', analiseviewsets.EstatisticasJogadoresView.as_view(), name='estatisticas-jogadores'),
    path('estatisticas_time/', analiseviewsets.EstatisticasTimeView.as_view(), name='estatisticas_time'),
]
