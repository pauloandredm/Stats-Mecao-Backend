from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from analise import models

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = models.CustomUser
        fields = ['id', 'nome', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
        }

    def create(self, validated_data):
        # Obtenha o valor da matricula a partir dos dados validados
        # Agora crie o usuário
        user = models.CustomUser(
            nome=validated_data['nome'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

class JogadorSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Jogador
        fields = '__all__'


class CampeonatoSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Campeonato
        fields = '__all__'


class TimeSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Time
        fields = '__all__'


class ConfrontoCreateSerializers(serializers.ModelSerializer):
    time_a = serializers.PrimaryKeyRelatedField(queryset=models.Time.objects.all())
    time_b = serializers.PrimaryKeyRelatedField(queryset=models.Time.objects.all(), allow_null=True)
    campeonato = serializers.PrimaryKeyRelatedField(queryset=models.Campeonato.objects.all())

    class Meta:
        model = models.Confronto
        fields = '__all__'


class ConfrontoViewSerializers(serializers.ModelSerializer):
    time_a = serializers.StringRelatedField()
    time_b = serializers.StringRelatedField(allow_null=True)
    campeonato = serializers.StringRelatedField()

    class Meta:
        model = models.Confronto
        fields = '__all__'


class EscalacaoSerializers(serializers.ModelSerializer):
    jogadores = serializers.SerializerMethodField()

    def get_jogadores(self, obj):
        apelidos_posicoes = {
            'Goleiro': 'GOL',
            'Lateral': 'LAT',
            'Zagueiro': 'ZAG',
            'Volante': 'VOL',
            'Meia': 'MEI',
            'Ponta': 'PON',
            'Atacante': 'ATA',
        }

        ordem_desejada = {
            'Goleiro': 1,
            'Lateral': 2,
            'Zagueiro': 3,
            'Volante': 4,
            'Meia': 5,
            'Ponta': 6,
            'Atacante': 7,
        }

        jogadores = obj.jogadores.all()
        jogadores_ordenados = sorted(jogadores, key=lambda jogador: ordem_desejada.get(jogador.posicao, 99))

        return [{'id': jogador.id, 'nome': jogador.nome, 'posicao': apelidos_posicoes.get(jogador.posicao, jogador.posicao)} for jogador in jogadores_ordenados]

    class Meta:
        model = models.Escalacao
        fields = '__all__'


class EscalacaoSerializers2(serializers.ModelSerializer):

    class Meta:
        model = models.Escalacao
        fields = '__all__'      

class EscalacaoCreateSerializers(serializers.ModelSerializer):
    confronto = serializers.PrimaryKeyRelatedField(queryset=models.Confronto.objects.all())
    jogadores = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Jogador.objects.all())

    class Meta:
        model = models.Escalacao
        fields = '__all__'

class SubstituicaoSerializer(serializers.ModelSerializer):
    jogador_saida = serializers.StringRelatedField()
    jogador_entrada = serializers.StringRelatedField()

    def get_jogadores(self, obj):
        return [{'id': jogador.id, 'nome': jogador.nome} for jogador in obj.jogadores.all()]

    class Meta:
        model = models.Substituicao
        fields = '__all__'


class SubstituicaoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Substituicao
        fields = ['confronto', 'jogador_entrada', 'jogador_saida', 'minuto', 'primeiro_tempo']


class LanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lance
        fields = '__all__'


class JogadorFezLanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Jogador
        fields = ['id', 'nome']


class NomeDoLanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tipo_Lance
        fields = ['tipo_lance']


class LanceSerializer2(serializers.ModelSerializer):
    jogador = JogadorFezLanceSerializer()  # Usando o novo serializer para a representação do jogador
    tipo_lance = NomeDoLanceSerializer()

    class Meta:
        model = models.Lance
        fields = ['id', 'minuto', 'tipo_lance', 'link_video', 'confronto', 'jogador', 'tempo']
        

class LanceCoordenadaSerializer(serializers.ModelSerializer):
    jogador = JogadorFezLanceSerializer()  # Usando o novo serializer para a representação do jogador
    tipo_lance = NomeDoLanceSerializer()
    
    class Meta:
        model = models.Lance
        fields = ['id', 'tipo_lance', 'jogador', 'minuto', 'coordenadaX', 'coordenadaY', 'coordenadaXFinal', 'coordenadaYFinal']
        

class ListaLancesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tipo_Lance
        fields = ['id', 'tipo_lance']

class JogadorOrdemSerializers(serializers.ModelSerializer):

    class Meta:
        model = models.Jogador
        fields = '__all__'

class ConfrontoPlacarSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Confronto
        fields = ['id', 'gols_time_a', 'gols_time_b']


class NomeDoCampSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Campeonato
        fields = ['nome']

class JogadorFezLanceFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Jogador
        fields = ['nome']


class LanceFiltroSerializer(serializers.ModelSerializer):
    nome_do_campeonato = serializers.SerializerMethodField()
    tipo_lance = NomeDoLanceSerializer()
    jogador = JogadorFezLanceFiltroSerializer()
    descricao_confronto = serializers.SerializerMethodField()

    class Meta:
        model = models.Lance
        fields = ['id', 'nome_do_campeonato', 'descricao_confronto', 'confronto', 'minuto', 'jogador', 'tipo_lance', 'coordenadaX', 'coordenadaY', 'coordenadaXFinal', 'coordenadaYFinal']
    
    def get_nome_do_campeonato(self, obj):
        return obj.confronto.campeonato.nome
    
    def get_descricao_confronto(self, obj):
        # Utiliza o método __str__ do modelo Confronto para obter a descrição
        return str(obj.confronto)


class ConfrontoAcrescimosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Confronto
        fields = ['id', 'acrescimo1tempo', 'acrescimo2tempo']


