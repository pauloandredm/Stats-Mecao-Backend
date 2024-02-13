from django.contrib import admin
from .models import CustomUser, Jogador, Campeonato, Time, Confronto, Escalacao, Substituicao, Lance, Tipo_Lance

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['id','nome', 'email']
    search_fields = ['nome', 'email']
admin.site.register(CustomUser, CustomUserAdmin)


class JogadorAdmin(admin.ModelAdmin):
    list_display = ['id','nome', 'posicao', 'data_nascimento', 'idade']
admin.site.register(Jogador, JogadorAdmin)


class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome']
admin.site.register(Campeonato, CampeonatoAdmin)


class TimeAdmin(admin.ModelAdmin):
    list_display = ['nome',]
admin.site.register(Time, TimeAdmin)


class ConfrontoAdmin(admin.ModelAdmin):
    list_display = ['id', 'time_a', 'gols_time_a', 'time_b', 'gols_time_b', 'campeonato', 'acrescimo1tempo', 'acrescimo2tempo']
admin.site.register(Confronto, ConfrontoAdmin)


class EscalacaoAdmin(admin.ModelAdmin):
    list_display = ['id', 'confronto', 'exibir_jogadores']

    def exibir_jogadores(self, obj):
        return ", ".join([str(jogador) for jogador in obj.jogadores.all()])
    
    exibir_jogadores.short_description = 'Jogadores'

admin.site.register(Escalacao, EscalacaoAdmin)


class SubstituicaoAdmin(admin.ModelAdmin):
    list_display = ['confronto', 'minuto', 'jogador_entrada', 'jogador_saida', 'primeiro_tempo']
admin.site.register(Substituicao, SubstituicaoAdmin)


class LanceAdmin(admin.ModelAdmin):
    list_display = ['confronto', 'minuto', 'jogador', 'tipo_lance', 'link_video',]
admin.site.register(Lance, LanceAdmin)


class TipoLanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'tipo_lance']
admin.site.register(Tipo_Lance, TipoLanceAdmin)