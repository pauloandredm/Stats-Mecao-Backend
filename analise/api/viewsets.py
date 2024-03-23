from rest_framework import viewsets, permissions
from analise.api import serializers
from analise import models
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from itertools import chain
from rest_framework.decorators import action, api_view
from django.shortcuts import get_object_or_404
from rest_framework import mixins
from django.db.models import Count, Case, When, IntegerField, Q, Value, F
from .filters import LanceFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes


class RegisterViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.RegisterSerializer
    queryset = models.CustomUser.objects.all()
    search_fields = ('name', 'cpf',)


class JogadorViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    serializer_class = serializers.JogadorSerializers
    queryset = models.Jogador.objects.all()


class CampeonatoViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.CampeonatoSerializers
    queryset = models.Campeonato.objects.all()
    

class TimeViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.TimeSerializers
    queryset = models.Time.objects.all()


class ConfrontoCreateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ConfrontoCreateSerializers

    def get_queryset(self):
        queryset = models.Confronto.objects.all()
        return queryset.select_related('time_a', 'time_b', 'campeonato')

    def create(self, request, *args, **kwargs):
        time_a_data = request.data.get('time_a')
        time_b_data = request.data.get('time_b')

        # Checa se time_a é um ID existente ou um nome de novo time
        if isinstance(time_a_data, str):
            time_a, created = models.Time.objects.get_or_create(nome=time_a_data)
            time_a_id = time_a.id
        else:
            time_a_id = time_a_data

        # Checa se time_b é um ID existente ou um nome de novo time
        if isinstance(time_b_data, str):
            time_b, created = models.Time.objects.get_or_create(nome=time_b_data)
            time_b_id = time_b.id
        else:
            time_b_id = time_b_data

        # Atualiza request.data com os IDs dos times
        request.data.update({'time_a': time_a_id, 'time_b': time_b_id})

        # Prossegue com a criação do confronto usando os IDs dos times
        return super().create(request, *args, **kwargs)
    
class ConfrontoViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ConfrontoViewSerializers

    def get_queryset(self):
        queryset = models.Confronto.objects.all()
        queryset = queryset.select_related('time_a', 'time_b', 'campeonato').order_by('-ano')

        return queryset


class EscalacaoViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    # retorna os 11 titulares iniciais
    serializer_class = serializers.EscalacaoSerializers
    queryset = models.Escalacao.objects.all()

    def get_queryset(self):
        confronto_id = self.request.query_params.get('confronto_id')
        if confronto_id:
            return models.Escalacao.objects.filter(confronto_id=confronto_id)
        return super().get_queryset()

    @action(detail=False, methods=['get'])
    def filtrar_por_confronto(self, request):
        confronto_id = request.query_params.get('confronto_id')
        if not confronto_id:
            return Response({"detail": "O parâmetro confronto_id é obrigatório."}, status=400)

        escalacoes = self.get_queryset().filter(confronto_id=confronto_id)
        serializer = self.get_serializer(escalacoes, many=True)
        return Response(serializer.data)


class EscalacaoCreateViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    serializer_class = serializers.EscalacaoCreateSerializers
    queryset = models.Escalacao.objects.all()


class EscalacaoConfrontoView(APIView):
    permission_classes = (IsAuthenticated,)
    
    # retorna os jogadores que estão em campo nesse minuto (titulares - subs_sairam + subs_entraram)
    # futuramente add expulsos
    def get(self, request, confronto_id, *args, **kwargs):

        escalacao = models.Escalacao.objects.filter(confronto_id=confronto_id).first()

        if not escalacao:
            # Retorna array vazio se não houver escalacao
            return Response([], status=status.HTTP_200_OK)
        
        substituicoes = models.Substituicao.objects.filter(confronto_id=confronto_id)
        jogadores_entrada_ids = substituicoes.values_list('jogador_entrada__id', flat=True)
        jogadores_saida_ids = substituicoes.values_list('jogador_saida__id', flat=True)

        jogadores_escalacao = escalacao.jogadores.all()
        jogadores_entrada = models.Jogador.objects.filter(id__in=jogadores_entrada_ids)

        # Junte os jogadores iniciais com os que entraram
        nova_lista_jogadores = list(chain(jogadores_escalacao, jogadores_entrada))

        # Exclua os jogadores que saíram da lista
        nova_lista_jogadores = [jogador for jogador in nova_lista_jogadores if jogador.id not in jogadores_saida_ids]
        
        # Buscar o jogador "Adversário" pelo ID e adicioná-lo à lista
        jogador_adversario = models.Jogador.objects.filter(id=16).first()
        if jogador_adversario:
            nova_lista_jogadores.append(jogador_adversario)

        # Ordenação dos jogadores por posição
        ordem_desejada = ['Goleiro', 'Lateral', 'Zagueiro', 'Volante', 'Meia', 'Ponta', 'Atacante']
        casos = [When(posicao=posicao, then=pos) for pos, posicao in enumerate(ordem_desejada)]
        jogadores_ordenados = sorted(nova_lista_jogadores, key=lambda jogador: ordem_desejada.index(jogador.posicao) if jogador.posicao in ordem_desejada else len(ordem_desejada))

        serializer = serializers.JogadorSerializers(jogadores_ordenados, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class EscalacaoConfrontoSemAdversarioView(APIView):
    permission_classes = (IsAuthenticated,)
    
    # retorna os jogadores que estão em campo nesse minuto (titulares - subs_sairam + subs_entraram)
    # futuramente add expulsos
    def get(self, request, confronto_id, *args, **kwargs):

        escalacao = models.Escalacao.objects.filter(confronto_id=confronto_id).first()

        if not escalacao:
            # Retorna array vazio se não houver escalacao
            return Response([], status=status.HTTP_200_OK)
        
        substituicoes = models.Substituicao.objects.filter(confronto_id=confronto_id)
        jogadores_entrada_ids = substituicoes.values_list('jogador_entrada__id', flat=True)
        jogadores_saida_ids = substituicoes.values_list('jogador_saida__id', flat=True)

        jogadores_escalacao = escalacao.jogadores.all()
        jogadores_entrada = models.Jogador.objects.filter(id__in=jogadores_entrada_ids)

        # Junte os jogadores iniciais com os que entraram
        nova_lista_jogadores = list(chain(jogadores_escalacao, jogadores_entrada))

        # Exclua os jogadores que saíram da lista
        nova_lista_jogadores = [jogador for jogador in nova_lista_jogadores if jogador.id not in jogadores_saida_ids]

        # Ordenação dos jogadores por posição
        ordem_desejada = ['Goleiro', 'Lateral', 'Zagueiro', 'Volante', 'Meia', 'Ponta', 'Atacante']
        casos = [When(posicao=posicao, then=pos) for pos, posicao in enumerate(ordem_desejada)]
        jogadores_ordenados = sorted(nova_lista_jogadores, key=lambda jogador: ordem_desejada.index(jogador.posicao) if jogador.posicao in ordem_desejada else len(ordem_desejada))

        serializer = serializers.JogadorSerializers(jogadores_ordenados, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)



class EscalacaoEditView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def put(self, request, confronto_id, *args, **kwargs):
        try:
            escalacao = models.Escalacao.objects.get(confronto_id=confronto_id)
            jogador_saida_id = request.data.get('jogador_saida_id')
            jogador_entrada_id = request.data.get('jogador_entrada_id')
            
            # Garanta que os IDs foram fornecidos
            if jogador_saida_id is None or jogador_entrada_id is None:
                return Response({"detail": "Os IDs de jogador_saida_id e jogador_entrada_id são obrigatórios."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            # Obtenha as instâncias dos jogadores
            jogador_saida = get_object_or_404(models.Jogador, pk=jogador_saida_id)
            jogador_entrada = get_object_or_404(models.Jogador, pk=jogador_entrada_id)


            # Adicione o jogador de entrada à escalação
            escalacao.jogadores.add(jogador_entrada)
            # Remova o jogador de saída da escalação
            escalacao.jogadores.remove(jogador_saida)

            # Serializar dados
            serializer = serializers.EscalacaoSerializers(escalacao)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except models.Escalacao.DoesNotExist:
            return Response({"detail": "Escalacao não encontrada para o confronto especificado."}, status=status.HTTP_404_NOT_FOUND)
        


class SubstituicaoViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Substituicao.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.SubstituicaoCreateSerializer
        return serializers.SubstituicaoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confronto = serializer.validated_data['confronto']
        jogador_saida_choices = models.Escalacao.objects.get(confronto=confronto).jogadores.all()

        # Atualize os campos do serializer com as escolhas
        serializer.fields['jogador_saida'].queryset = jogador_saida_choices

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

class JogadoresForaEscalacaoView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, confronto_id, *args, **kwargs):
        escalacao = models.Escalacao.objects.filter(confronto_id=confronto_id).first()

        if not escalacao:
            # Retorna array vazio se não houver escalacao
            return Response([], status=status.HTTP_200_OK)

        substituicoes = models.Substituicao.objects.filter(confronto_id=confronto_id)

        # Obtém todos os jogadores do time
        todos_jogadores = models.Jogador.objects.all()

        # Obtém os IDs dos jogadores na escalacao e na lista de jogador_entrada das substituicoes
        jogadores_na_escalacao_ids = escalacao.jogadores.values_list('id', flat=True)
        jogadores_entrada_ids = substituicoes.values_list('jogador_entrada__id', flat=True)
        adversario = [16]

        # Combina os dois conjuntos de IDs
        ids_para_excluir = list(jogadores_na_escalacao_ids) + list(jogadores_entrada_ids) + adversario

        # Filtra os jogadores que não estão na escalacao ou na lista de jogador_entrada das substituicoes
        jogadores_fora_escalacao = todos_jogadores.exclude(id__in=ids_para_excluir)

        # Serializa os jogadores
        serializer = serializers.JogadorSerializers(jogadores_fora_escalacao, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

        

class SubstituicaoConfrontoViewSet(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, confronto_id, *args, **kwargs):  
        try:
            substituicoes = models.Substituicao.objects.filter(confronto_id=confronto_id).order_by('minuto')
            serializer = serializers.SubstituicaoSerializer(substituicoes, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except models.Substituicao.DoesNotExist:
            return Response({"detail": "Substituicao não encontrada para o confronto especificado."}, status=status.HTTP_404_NOT_FOUND)
    

class JogadoresNaoTitularViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    
    # Retorna jogadores que não foram titulares nesse confronto (usado para o edit escalação)
    serializer_class = serializers.JogadorSerializers

    def list(self, request, *args, **kwargs):
        confronto_id = self.request.query_params.get('confronto_id')

        if confronto_id is None:
            return Response({"detail": "O parâmetro confronto_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            titulares = models.Escalacao.objects.filter(confronto_id=confronto_id).values_list('jogadores', flat=True)
            jogadores_nao_titulares = models.Jogador.objects.exclude(id__in=titulares)
            serializer = self.serializer_class(jogadores_nao_titulares, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except models.Escalacao.DoesNotExist:
            return Response({"detail": "Confronto não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        

class LanceViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Lance.objects.all()
    serializer_class = serializers.LanceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def filtrar_por_confronto(self, request):
        confronto_id = request.query_params.get('confronto_id')
        if not confronto_id:
            return Response({"detail": "O parâmetro confronto_id é obrigatório."}, status=400)

        lances = self.queryset.filter(confronto_id=confronto_id).order_by('-tempo', '-minuto', '-id')
        serializer = serializers.LanceSerializer2(lances, many=True)
        return Response(serializer.data)
    

class TiposLancesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Tipo_Lance.objects.all()
    serializer_class = serializers.ListaLancesSerializer


@api_view(['DELETE'])
def remover_jogador(request, confronto_id, jogador_id):
    permission_classes = (IsAuthenticated,)
    
    try:
        escalacao = models.Escalacao.objects.get(confronto_id=confronto_id)
        jogador = models.Jogador.objects.get(id=jogador_id)

        # Remover o jogador da escalacao
        escalacao.jogadores.remove(jogador)

        return Response(status=status.HTTP_204_NO_CONTENT)

    except models.Escalacao.DoesNotExist:
        return Response({"detail": "Escalacao não encontrada."}, status=status.HTTP_404_NOT_FOUND)

    except models.Jogador.DoesNotExist:
        return Response({"detail": "Jogador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST', 'PUT'])
def adicionar_jogador(request, confronto_id, jogador_id):
    permission_classes = (IsAuthenticated,)
    
    try:
        confronto = models.Confronto.objects.get(id=confronto_id)

        try:
            # Tenta encontrar uma escalacao existente para o confronto
            escalacao = models.Escalacao.objects.get(confronto=confronto)
        except models.Escalacao.DoesNotExist:
            # Se não existir, cria uma nova escalacao para o confronto
            escalacao = models.Escalacao.objects.create(confronto=confronto)

        jogador = models.Jogador.objects.get(id=jogador_id)

        # Adiciona o jogador à escalacao
        escalacao.jogadores.add(jogador)

        # Serializa e retorna a escalacao
        serializer = serializers.EscalacaoSerializers2(escalacao)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except models.Confronto.DoesNotExist:
        return Response({"detail": "Confronto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

    except models.Jogador.DoesNotExist:
        return Response({"detail": "Jogador não encontrado."}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['GET'])
def jogadores_disponiveis(request, confronto_id):
    permission_classes = (IsAuthenticated,)
    
    try:
        confronto = models.Confronto.objects.get(id=confronto_id)
    except models.Confronto.DoesNotExist:
        return Response({"detail": "Confronto não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Verifica se existe uma escalacao para o confronto
    try:
        escalacao = models.Escalacao.objects.get(confronto=confronto)
        jogadores_na_escalacao = escalacao.jogadores.all()
    except models.Escalacao.DoesNotExist:
        jogadores_na_escalacao = []

    POSICAO_ORDENACAO = {
        'Goleiro': 1,
        'Lateral': 2,
        'Zagueiro': 3,
        'Volante': 4,
        'Meia': 5,
        'Ponta': 6,
        'Atacante': 7,
    }

    # Ordena os jogadores disponíveis conforme a ordem de posição
    ordenacao_case = Case(*[When(posicao=posicao, then=Value(ordem)) for posicao, ordem in POSICAO_ORDENACAO.items()], default=Value(8), output_field=IntegerField())
    jogadores_disponiveis = models.Jogador.objects.exclude(id__in=[jogador.id for jogador in jogadores_na_escalacao] + [16]).annotate(ordenacao=ordenacao_case).order_by('ordenacao')

    serializer = serializers.JogadorOrdemSerializers(jogadores_disponiveis, many=True)
    
    return Response(serializer.data)


class LanceCoordenadaViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Lance.objects.all()
    serializer_class = serializers.LanceCoordenadaSerializer

    @action(detail=False, methods=['get'])
    def filtrar_por_confronto(self, request):
        confronto_id = request.query_params.get('confronto_id')
        jogador_id = request.query_params.get('jogador')
        tipo_lance_ids = request.query_params.getlist('tipo_lance')  # Usa getlist para pegar uma lista de valores
        tempo = request.query_params.get('tempo')
        campo = request.query_params.get('campo')

        # Filtrar por confronto
        lances = self.queryset.filter(confronto_id=confronto_id)
        
        # Filtrar por jogador, se fornecido
        if jogador_id:
            lances = lances.filter(jogador_id=jogador_id)

        # Filtrar por tipo de lance, se fornecido
        if tipo_lance_ids:
            lances = lances.filter(tipo_lance_id__in=tipo_lance_ids)  # Filtrar por múltiplos IDs usando __in

        # Filtrar por tempo
        if tempo == "1":
            lances = lances.filter(tempo__in=[1, 0])  # Inclui lances sem tempo definido (tempo=0)
        elif tempo == "2":
            lances = lances.filter(tempo=2)

        # Filtrar por campo
        if campo == "defesa":
            lances = lances.filter(coordenadaX__gt=300)
        elif campo == "ataque":
            lances = lances.filter(coordenadaX__lte=300)
            

        serializer = self.get_serializer(lances, many=True)
        return Response(serializer.data)
    

class ConfrontoPlacarViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Confronto.objects.all()
    serializer_class = serializers.ConfrontoPlacarSerializer

    @action(detail=False, methods=['patch'])
    def filtrar_por_confronto(self, request, confronto_id):
        placar = self.queryset.filter(confronto_id=confronto_id)
        serializer = self.get_serializer(placar, many=True)
        return Response(serializer.data)
    

class LanceFilterViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Lance.objects.all()
    serializer_class = serializers.LanceFiltroSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        campeonato_ids = self.request.query_params.getlist('campeonato')
        tipo_lance_ids = self.request.query_params.getlist('tipo_lance')
        jogador_ids = self.request.query_params.getlist('jogador')
        jogo_ids = self.request.query_params.getlist('jogo')
        minuto_inicio = self.request.query_params.get('minuto_inicio', 0)
        minuto_fim = self.request.query_params.get('minuto_fim', 1000)
        """ coordenadaX_inicio = self.request.query_params.get('coordenadaX_inicio')
        coordenadaY_inicio = self.request.query_params.get('coordenadaY_inicio')
        coordenadaX_fim = self.request.query_params.get('coordenadaX_fim')
        coordenadaY_fim = self.request.query_params.get('coordenadaY_fim') """

        if campeonato_ids:
            queryset = queryset.filter(confronto__campeonato__id__in=campeonato_ids)
        if tipo_lance_ids:
            queryset = queryset.filter(tipo_lance__id__in=tipo_lance_ids)
        if jogador_ids:
            queryset = queryset.filter(jogador__id__in=jogador_ids)
        if jogo_ids:
            queryset = queryset.filter(confronto__id__in=jogo_ids)

        queryset = queryset.filter(minuto__gte=minuto_inicio, minuto__lte=minuto_fim)

        # Para a filtragem por coordenadas, você precisará definir uma lógica
        # específica que considere os limites do retângulo formado pelas coordenadas de início e fim
        """ if coordenadaX_inicio and coordenadaY_inicio and coordenadaX_fim and coordenadaY_fim:
            queryset = queryset.filter(
                coordenadaX__gte=coordenadaX_inicio, coordenadaX__lte=coordenadaX_fim,
                coordenadaY__gte=coordenadaY_inicio, coordenadaY__lte=coordenadaY_fim
            ) """
        
        return queryset
    

class ConfrontoAcrescimosViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    
    queryset = models.Confronto.objects.all()
    serializer_class = serializers.ConfrontoAcrescimosSerializer

    def partial_update(self, request, pk=None):
        confronto = self.get_object()
        serializer = self.get_serializer(confronto, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def jogadores_no_confronto(request, confronto_id):
    permission_classes = (IsAuthenticated,)
    
    try:
        confronto = models.Confronto.objects.get(id=confronto_id)
    except models.Confronto.DoesNotExist:
        return Response({'detail': 'Confronto não encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    # Pega todos os jogadores que foram escalados para o confronto
    jogadores_escalados = models.Jogador.objects.filter(escalacoes__confronto=confronto).distinct()
    
    # Pega todos os jogadores que entraram como substitutos no confronto
    jogadores_substitutos = models.Jogador.objects.filter(substituicoes_entrada__confronto=confronto).distinct()
    
    # Combina os dois querysets de jogadores
    todos_jogadores = jogadores_escalados | jogadores_substitutos

    # Serializa os dados. Supondo que você tenha um serializer chamado JogadorSerializer
    serializer = serializers.JogadorSerializers(todos_jogadores, many=True)
    
    return Response(serializer.data)




























class EstatisticasJogadoresView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        filtered_lances = LanceFilter(request.GET, queryset=models.Lance.objects.all()).qs
        jogadores = models.Jogador.objects.exclude(id=16)

        # Recupera o ID do campeonato do parâmetro da query, se existir
        campeonato_id = request.query_params.get('campeonato')
        jogo_id = request.query_params.get('jogo')

        estatisticas = []
        for jogador in jogadores:

            jogador_lances = filtered_lances.filter(jogador=jogador)

            # desempenho
            gols = jogador_lances.filter(tipo_lance__tipo_lance='Gol').count()
            gols_de_penalti = jogador_lances.filter(tipo_lance__tipo_lance='Gol de Penalti').count()
            assistencias = jogador_lances.filter(tipo_lance__tipo_lance='Assistencia').count()
            chute_pra_fora = jogador_lances.filter(tipo_lance__tipo_lance='Finalização pra fora').count()
            chute_defendido = jogador_lances.filter(tipo_lance__tipo_lance='Finalização defendida').count()
            chute_na_trave = jogador_lances.filter(tipo_lance__tipo_lance='Finalização na trave').count()
            impedimento = jogador_lances.filter(tipo_lance__tipo_lance='Impedimento').count()

            # desempenho defensivo
            cartao_amarelo = jogador_lances.filter(tipo_lance__tipo_lance='Cartão Amarelo').count()
            cartao_vermelho = jogador_lances.filter(tipo_lance__tipo_lance='Cartão Vermelho').count()
            desarme = jogador_lances.filter(tipo_lance__tipo_lance='Desarme').count()
            roubada_de_bola = jogador_lances.filter(tipo_lance__tipo_lance='Roubada de Bola').count()
            falta_cometida = jogador_lances.filter(tipo_lance__tipo_lance='Falta cometida').count()
            falta_sofrida = jogador_lances.filter(tipo_lance__tipo_lance='Falta sofrida').count()
            falta_cartao_sofrida = jogador_lances.filter(tipo_lance__tipo_lance='Falta sofrida para cartão').count()


            # esperado
            gols_esperados = jogador_lances.filter(tipo_lance__tipo_lance='Chance de Gol').count()
            assists_esperados = jogador_lances.filter(tipo_lance__tipo_lance='Chance de Assistencia').count()

            # progressao
            progressao_solo = jogador_lances.filter(tipo_lance__tipo_lance='Progressão com a bola').count()
            passe_ql = jogador_lances.filter(tipo_lance__tipo_lance='Passe Quebra linha').count()
            passe_ql_recebido = jogador_lances.filter(tipo_lance__tipo_lance='Passe QL recebido').count()

            # Aplica o filtro de campeonato na contagem de partidas titulares e partidas jogadas, se um campeonato foi especificado
            if jogo_id:
                partidas_titulares = models.Escalacao.objects.filter(
                    jogadores=jogador,
                    confronto__id=jogo_id  # Filtra escalacoes pelo campeonato especificado
                ).distinct().count()

                partidas_substituido = models.Substituicao.objects.filter(
                    jogador_entrada=jogador,
                    confronto__id=jogo_id
                ).distinct().count()
            
            elif campeonato_id:
                partidas_titulares = models.Escalacao.objects.filter(
                    jogadores=jogador,
                    confronto__campeonato_id=campeonato_id  # Filtra escalacoes pelo campeonato especificado
                ).distinct().count()

                partidas_substituido = models.Substituicao.objects.filter(
                    jogador_entrada=jogador,
                    confronto__campeonato_id=campeonato_id
                ).distinct().count()
        
            else:
                partidas_titulares = models.Escalacao.objects.filter(
                    jogadores=jogador
                ).distinct().count()

                partidas_substituido = models.Substituicao.objects.filter(
                    jogador_entrada=jogador
                ).distinct().count()
            
            partidas_jogadas = partidas_titulares + partidas_substituido



            ####### calculo do tempo de minutos jogador
            minutos_totais = 0

            if campeonato_id:

                confrontos_jogador_titular = models.Confronto.objects.filter(
                    escalacao__jogadores=jogador,
                    campeonato_id=campeonato_id
                ).distinct()

                confrontos_jogador_entrou = models.Confronto.objects.filter(
                    substituicao__jogador_entrada=jogador,
                    campeonato_id=campeonato_id
                ).distinct()

                confrontos_totais = confrontos_jogador_titular.union(confrontos_jogador_entrou)

                for confronto in confrontos_totais:
                    foi_substituido = models.Substituicao.objects.filter(
                        confronto=confronto, jogador_saida=jogador
                    ).exists()
                    entrou_como_substituto = models.Substituicao.objects.filter(
                        confronto=confronto, jogador_entrada=jogador
                    ).first()

                    foi_expulso = models.Lance.objects.filter(confronto=confronto, jogador=jogador, tipo_lance=11,).distinct().first()

                    if foi_substituido:
                        substituicao = models.Substituicao.objects.get(confronto=confronto, jogador_saida=jogador)
                        if substituicao.primeiro_tempo:
                            minutos_totais += substituicao.minuto
                        else:
                            minutos_totais += substituicao.minuto + confronto.acrescimo1tempo
                    elif entrou_como_substituto:
                        if foi_expulso:
                            if foi_expulso.tempo < 2: # expulso no primeiro tempo
                                minutos_totais += foi_expulso.minuto - entrou_como_substituto.minuto
                            else: # expulso no segundo tempo
                                minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo - entrou_como_substituto.minuto
                        else:
                            if entrou_como_substituto.primeiro_tempo:
                                minutos_totais += 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo - entrou_como_substituto.minuto
                            else:
                                minutos_totais += 90 + confronto.acrescimo2tempo - entrou_como_substituto.minuto
                    else: # titular e não saiu
                        if foi_expulso:
                            if foi_expulso.tempo < 2: # expulso no primeiro tempo
                                minutos_totais += foi_expulso.minuto
                            else: # expulso no segundo tempo
                                minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo
                        else:
                            minutos_totais += 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo
            
            elif jogo_id:

                confrontos_jogador_titular = models.Confronto.objects.filter(
                    id = jogo_id, escalacao__jogadores=jogador,
                ).distinct()

                confrontos_jogador_entrou = models.Confronto.objects.filter(
                    id = jogo_id, substituicao__jogador_entrada=jogador,
                ).distinct()

                foi_expulso = models.Lance.objects.filter(confronto=jogo_id, jogador=jogador, tipo_lance=11,).distinct().first()

                try:
                    confronto = models.Confronto.objects.get(id=jogo_id)
                except models.Confronto.DoesNotExist:
                    # Trate o caso em que o confronto não existe
                    # Por exemplo, retornando uma resposta de erro
                    return Response({"error": "Confronto não encontrado."}, status=status.HTTP_404_NOT_FOUND)

                # Depois, verifique as condições relacionadas ao jogador sendo titular, entrando ou saindo
                if confrontos_jogador_titular.exists():
                    substituicao_saida = models.Substituicao.objects.filter(confronto=confronto, jogador_saida=jogador).first()
                    if foi_expulso:
                        if foi_expulso.tempo < 2: # expulso no primeiro tempo
                            minutos_totais += foi_expulso.minuto
                        else: # expulso no segundo tempo
                            minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo

                    elif substituicao_saida:
                        if substituicao_saida.primeiro_tempo:
                            minutos_totais = substituicao_saida.minuto
                        else:
                            minutos_totais = substituicao_saida.minuto + confronto.acrescimo1tempo
                    else:
                        minutos_totais = 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo

                elif confrontos_jogador_entrou.exists():
                    substituicao_entrada = models.Substituicao.objects.filter(confronto=confronto, jogador_entrada=jogador).first()
                    if foi_expulso:
                        if foi_expulso.tempo < 2: # expulso no primeiro tempo
                            minutos_totais += foi_expulso.minuto
                        else: # expulso no segundo tempo
                            minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo
                    elif substituicao_entrada:
                        if substituicao_entrada.primeiro_tempo:
                            minutos_totais = 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo - substituicao_entrada.minuto
                        else:
                            minutos_totais = 90 + confronto.acrescimo2tempo - substituicao_entrada.minuto

            else: #sem nenhum filtro

                confrontos_jogador_titular = models.Confronto.objects.filter(
                    escalacao__jogadores=jogador,
                ).distinct()

                confrontos_jogador_entrou = models.Confronto.objects.filter(
                    substituicao__jogador_entrada=jogador,
                ).distinct()

                confrontos_totais = confrontos_jogador_titular.union(confrontos_jogador_entrou)

                for confronto in confrontos_totais:
                    foi_substituido = models.Substituicao.objects.filter(
                        confronto=confronto, jogador_saida=jogador
                    ).exists()
                    entrou_como_substituto = models.Substituicao.objects.filter(
                        confronto=confronto, jogador_entrada=jogador
                    ).first()

                    foi_expulso = models.Lance.objects.filter(confronto=confronto, jogador=jogador, tipo_lance=11,).distinct().first()

                    if foi_substituido:
                        substituicao = models.Substituicao.objects.get(confronto=confronto, jogador_saida=jogador)
                        if substituicao.primeiro_tempo:
                            minutos_totais += substituicao.minuto
                        else:
                            minutos_totais += substituicao.minuto + confronto.acrescimo1tempo
                    elif entrou_como_substituto:
                        if foi_expulso:
                            if foi_expulso.tempo < 2: # expulso no primeiro tempo
                                minutos_totais += foi_expulso.minuto
                            else: # expulso no segundo tempo
                                minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo
                        else:
                            if entrou_como_substituto.primeiro_tempo:
                                minutos_totais += 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo - entrou_como_substituto.minuto
                            else:
                                minutos_totais += 90 + confronto.acrescimo2tempo - entrou_como_substituto.minuto
                    else:
                        if foi_expulso:
                            if foi_expulso.tempo < 2: # expulso no primeiro tempo
                                minutos_totais += foi_expulso.minuto
                            else: # expulso no segundo tempo
                                minutos_totais += foi_expulso.minuto + confronto.acrescimo1tempo
                        else:
                            minutos_totais += 90 + confronto.acrescimo1tempo + confronto.acrescimo2tempo

            if partidas_jogadas == 0:
                media_minutos = 0
            else: 
                media_minutos = round((minutos_totais/partidas_jogadas),2)
            
            ############ fim calculo tempo

            # desempenho
            gols_total = gols + gols_de_penalti
            faltas_sofridas = falta_sofrida + falta_cartao_sofrida
            faltas_cometidas = falta_cometida + cartao_amarelo + cartao_vermelho

            # esperado
            """ gols_assists_esperados = gols_esperados + assists_esperados """
            # per 90 min
            if minutos_totais == 0:
                minutos_totais = 0.0000000001

            tempo_div_90 = minutos_totais/90

            gols_p_90min = round((gols_total/tempo_div_90), 3)
            assists_p_90min = round((assistencias/tempo_div_90), 3)
            gols_assists_p_90min = gols_p_90min + assists_p_90min
            gols_esperados_p_90min = round((gols_esperados/tempo_div_90), 3)
            assists_esperados_p_90min = round((assists_esperados/tempo_div_90), 3)
            finalizacoes_p_90min = round(((chute_pra_fora + chute_defendido + chute_na_trave + gols_total)/tempo_div_90), 3)
            falta_sofrida_p_90 = round(((faltas_sofridas)/tempo_div_90), 3)
            progressoes_p_90 = round(((progressao_solo + passe_ql_recebido + passe_ql)/tempo_div_90), 3)
            rb_desarme_p_90 = round(((roubada_de_bola + desarme)/tempo_div_90), 3)
            cartoes_p_90 = round(((cartao_amarelo + cartao_vermelho)/tempo_div_90), 3)
            falta_cometida_p_90 = round(((faltas_cometidas)/tempo_div_90), 3)



            estatisticas.append({
                # info
                'nome': jogador.nome,
                'posicao': jogador.posicao,

                # tempo
                'partidas_titulares': partidas_titulares,
                'partidas_jogadas': partidas_jogadas,
                'minutos_totais': int(minutos_totais),
                'media_minutos': media_minutos,

                # desempenho
                'gols': gols_total,
                'assistencias': assistencias,
                'chutes_pra_fora': chute_pra_fora,
                'chutes_defendidos': chute_defendido,
                'chutes_na_trave': chute_na_trave,
                'impedimentos': impedimento,

                # desempenho defensivo
                'cartao_amarelo': cartao_amarelo,
                'cartao_vermelho': cartao_vermelho,
                'desarmes': desarme,
                'roubada_de_bola': roubada_de_bola,
                'faltas_cometida': faltas_cometidas,
                'faltas_sofridas': faltas_sofridas,

                # esperado
                'gols_esperados': gols_esperados,
                'assistencias_esperados': assists_esperados,

                # progressao
                'progressao_com_a_bola': progressao_solo,
                'passe_quebra_linha': passe_ql,
                'passe_ql_recebido': passe_ql_recebido,

                # a cada 90min
                'gols_p_90min': gols_p_90min,
                'assists_p_90min': assists_p_90min,
                'Gols_assists_p_90min': gols_assists_p_90min,
                'gols_esperados_p_90min': gols_esperados_p_90min,
                'assists_esperados_p_90min': assists_esperados_p_90min,
                'finalizacoes_p_90_min':  finalizacoes_p_90min,
                'falta_sofrida_p_90': falta_sofrida_p_90,
                'progressoes_p_90': progressoes_p_90,
                'rb_desarme_p_90': rb_desarme_p_90,
                'cartoes_p_90': cartoes_p_90,
                'falta_cometida_p_90': falta_cometida_p_90,

                # Adicione mais estatísticas conforme necessário
            })

        return Response(estatisticas)


















class EstatisticasTimeView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        filtered_lances = LanceFilter(request.GET, queryset=models.Lance.objects.all()).qs

        campeonato_id = request.query_params.get('campeonato')
        jogo_id = request.query_params.get('jogo')

        estatisticas_time = {
            # desempenho
            'partidas_jogadas': 0,
            'gols': 0,
            'assistencias': 0,
            'gols_assistencias': 0,
            'penaltis_batidos': 0,
            'gols_de_penalti': 0,
            'finalizacoes_pra_fora': 0,
            'finalizacoes_defendidas': 0,
            'finalizacoes_na_trave': 0,
            'impedimentos': 0,
            'faltas_sofridas': 0,
            'falta_pra_cartao_sofrida': 0,
            # desempenho defensivo
            'cartao_amarelo': 0,
            'cartao_vermelho': 0,
            'roubadas_de_bola': 0,
            'desarmes': 0,
            'faltas_cometidas': 0,
            'finalizacoes_sofridas': 0,
            'finalizacoes_perigosas_sofridas': 0,
            'gol_sofrido': 0,
            # chances de gols/esperado
            'gols_esperados': 0,
            'assists_esperados': 0,
            'gols_assists_esperados': 0,
            # progressao
            'progressao_solo': 0,
            'passe_ql': 0,
            'passe_ql_recebido': 0,
            # a cada 90min
            'gols_p_90min': 0,
            'assists_p_90min': 0,
            'gols_assists_p_90min': 0,
            'gols_esperados_p_90min': 0,
            'assists_esperados_p_90min': 0,
            'gols_assists_esperados_p_90min': 0,
            'finalizacoes_p_90min': 0,
            'faltas_sofrida_p_90min': 0,
            'cartoes_causados_p_90': 0,
            'cartoes_sofridos_p_90min': 0,
            'rb_desarme_p_90min': 0,
            'falta_cometida_p_90min': 0,
            'finalizacoes_sofridas_p_90min': 0,
            'finalizacoes_perigosas_sofridas_p_90min': 0,
            'gols_sofridos_p_90min': 0,
        }

        ############### pegando os dados para o response ###############

        # tempo
        if jogo_id:
            estatisticas_time['partidas_jogadas'] = models.Confronto.objects.filter(id=jogo_id).count()
        elif campeonato_id:
            estatisticas_time['partidas_jogadas'] = models.Confronto.objects.filter(campeonato_id=campeonato_id).count()
        else:
            estatisticas_time['partidas_jogadas'] = models.Confronto.objects.count()

        if estatisticas_time['partidas_jogadas'] == 0:
            estatisticas_time['partidas_jogadas']=0.000000001

        # desempenho
        gols_normais = filtered_lances.filter(tipo_lance__tipo_lance='Gol').count()
        gols_de_penalti = filtered_lances.filter(tipo_lance__tipo_lance='Gol de Penalti').count()
        assists = filtered_lances.filter(tipo_lance__tipo_lance='Assistencia').count()
        penaltis_batidos = filtered_lances.filter(tipo_lance__tipo_lance='Penalti perdido').count()
        chute_pra_fora = filtered_lances.filter(tipo_lance__tipo_lance='Finalização pra fora').count()
        chute_na_trave = filtered_lances.filter(tipo_lance__tipo_lance='Finalização na trave').count()
        chute_defendido = filtered_lances.filter(tipo_lance__tipo_lance='Finalização defendida').count()
        impedimento = filtered_lances.filter(tipo_lance__tipo_lance='Impedimento').count()
        falta_sofrida = filtered_lances.filter(tipo_lance__tipo_lance='Falta sofrida').count()
        falta_s_p_cartao = filtered_lances.filter(tipo_lance__tipo_lance='Falta sofrida para cartão').count()
        # desempenho defensivo
        cartao_amarelo = filtered_lances.filter(tipo_lance__tipo_lance='Cartão Amarelo').count()
        cartao_vermelho = filtered_lances.filter(tipo_lance__tipo_lance='Cartão Vermelho').count()
        rb = filtered_lances.filter(tipo_lance__tipo_lance='Roubada de Bola').count()
        desarmes = filtered_lances.filter(tipo_lance__tipo_lance='Desarmes').count()
        falta_cometida = filtered_lances.filter(tipo_lance__tipo_lance='Falta cometida').count()
        fin_sofrida = filtered_lances.filter(tipo_lance__tipo_lance='Finalização normal sofrida').count()
        fin_s_perigosa = filtered_lances.filter(tipo_lance__tipo_lance='Finalização perigosa sofrida').count()
        gol_sofrido = filtered_lances.filter(tipo_lance__tipo_lance='Gol sofrido').count()
        # chances de gols/esperado
        gols_esperados = filtered_lances.filter(tipo_lance__tipo_lance='Chance de Gol').count()
        assists_esperados = filtered_lances.filter(tipo_lance__tipo_lance='Chance de Assistencia').count()
        # progressao
        progressao_solo = filtered_lances.filter(tipo_lance__tipo_lance='Progressão com a bola').count()
        passe_ql = filtered_lances.filter(tipo_lance__tipo_lance='Passe Quebra linha').count()
        passe_ql_recebido = filtered_lances.filter(tipo_lance__tipo_lance='Passe QL recebido').count()


        ############### passando dados para o response ###############

        # desempenho
        estatisticas_time['gols'] = gols_normais + gols_de_penalti
        estatisticas_time['assistencias'] = assists
        estatisticas_time['gols_assistencias'] = gols_normais + gols_de_penalti + assists
        estatisticas_time['penaltis_batidos'] = penaltis_batidos + gols_de_penalti
        estatisticas_time['gols_de_penalti'] = gols_de_penalti
        estatisticas_time['finalizacoes_pra_fora'] = chute_pra_fora
        estatisticas_time['finalizacoes_defendidas'] = chute_defendido
        estatisticas_time['finalizacoes_na_trave'] = chute_na_trave
        estatisticas_time['impedimentos'] = impedimento
        estatisticas_time['faltas_sofridas'] = falta_sofrida + falta_s_p_cartao
        estatisticas_time['falta_pra_cartao_sofrida'] = falta_s_p_cartao
        # desempenho defensivo
        estatisticas_time['cartao_amarelo'] = cartao_amarelo
        estatisticas_time['cartao_vermelho'] = cartao_vermelho
        estatisticas_time['roubadas_de_bola'] = rb
        estatisticas_time['desarmes'] = desarmes
        estatisticas_time['faltas_cometidas'] = falta_cometida + cartao_amarelo + cartao_vermelho
        estatisticas_time['finalizacoes_sofridas'] = fin_sofrida + fin_s_perigosa + gol_sofrido
        estatisticas_time['finalizacoes_perigosas_sofridas'] = fin_s_perigosa
        estatisticas_time['gol_sofrido'] = gol_sofrido
        # chances de gols/esperado
        estatisticas_time['gols_esperados'] = gols_esperados
        estatisticas_time['assists_esperados'] = assists_esperados
        estatisticas_time['gols_assists_esperados'] = gols_esperados + assists_esperados
        # progressao
        estatisticas_time['progressao_solo'] = progressao_solo
        estatisticas_time['passe_ql'] = passe_ql
        estatisticas_time['passe_ql_recebido'] = passe_ql_recebido
        # a cada 90min
        estatisticas_time['gols_p_90min'] = round(((gols_normais + gols_de_penalti)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['assists_p_90min'] = round((assists/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['gols_assists_p_90min'] = estatisticas_time['assists_p_90min'] + estatisticas_time['gols_p_90min']
        estatisticas_time['gols_esperados_p_90min'] = round((gols_esperados/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['assists_esperados_p_90min'] = round((assists_esperados/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['gols_assists_esperados_p_90min'] = estatisticas_time['gols_esperados_p_90min'] + estatisticas_time['assists_esperados_p_90min']
        estatisticas_time['finalizacoes_p_90min'] = round(((chute_pra_fora + chute_na_trave + chute_defendido + gols_normais + gols_de_penalti)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['faltas_sofrida_p_90min'] = round(((falta_sofrida + falta_s_p_cartao)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['cartoes_causados_p_90'] = round(((falta_s_p_cartao)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['cartoes_sofridos_p_90min'] = round(((cartao_amarelo + cartao_vermelho)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['rb_desarme_p_90min'] = round(((rb + desarmes)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['falta_cometida_p_90min'] = round(((falta_cometida + cartao_amarelo + cartao_vermelho)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['finalizacoes_sofridas_p_90min'] = round(((fin_sofrida)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['finalizacoes_perigosas_sofridas_p_90min'] = round(((fin_s_perigosa)/estatisticas_time['partidas_jogadas']),3)
        estatisticas_time['gols_sofridos_p_90min'] = round(((gol_sofrido)/estatisticas_time['partidas_jogadas']),3)
        # Adicione lógica para calcular partidas jogadas, se necessário

        return Response(estatisticas_time)
