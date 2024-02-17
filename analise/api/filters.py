import django_filters
from analise import models

class LanceFilter(django_filters.FilterSet):
    campeonato = django_filters.NumberFilter(field_name='confronto__campeonato__id')
    minuto_inicio = django_filters.NumberFilter(field_name='minuto', lookup_expr='gte')
    minuto_fim = django_filters.NumberFilter(field_name='minuto', lookup_expr='lte')
    """ tipo_lance = django_filters.NumberFilter(field_name='tipo_lance__id')
    jogador = django_filters.NumberFilter(field_name='jogador__id') """
    jogo = django_filters.NumberFilter(field_name='confronto__id')

    class Meta:
        model = models.Lance
        fields = ['campeonato', 'minuto_inicio', 'minuto_fim']
        """ fields = ['campeonato', 'tipo_lance', 'jogador', 'jogo', 'minuto_inicio', 'minuto_fim'] """
