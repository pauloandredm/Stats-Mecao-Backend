from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import datetime
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O campo de e-mail é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, nome, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nome = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    def __str__(self):
        return self.email


class Jogador(models.Model):
    POSICOES_CHOICES = [
        ('Goleiro', 'Goleiro'),
        ('Lateral', 'Lateral'),
        ('Zagueiro', 'Zagueiro'),
        ('Volante', 'Volante'),
        ('Meia', 'Meia'),
        ('Ponta', 'Ponta'),
        ('Atacante', 'Atacante'),
    ]

    nome = models.CharField(max_length=255)
    posicao = models.CharField(max_length=20, choices=POSICOES_CHOICES)
    data_nascimento = models.DateField(null=True)

    def idade(self):
        if self.data_nascimento:
            hoje = datetime.now().date()
            delta = hoje - self.data_nascimento
            idade = delta.days // 365
            return idade
        return None
    
    def __str__(self):
        return self.nome
    

class Campeonato(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Time(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome


class Confronto(models.Model):
    time_a = models.ForeignKey(Time, related_name='confrontos_time_a', on_delete=models.CASCADE)
    time_b = models.ForeignKey(Time, related_name='confrontos_time_b', on_delete=models.CASCADE, null=True, blank=True)
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE)
    ano = models.DateField()
    gols_time_a = models.IntegerField(default=0)
    gols_time_b = models.IntegerField(default=0)
    acrescimo1tempo = models.IntegerField(default=0)
    acrescimo2tempo = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.time_a.nome} {self.gols_time_a} vs {self.gols_time_b} {self.time_b.nome if self.time_b else 'N/A'}"


class Escalacao(models.Model):
    confronto = models.ForeignKey(Confronto, on_delete=models.CASCADE)
    jogadores = models.ManyToManyField(Jogador, related_name='escalacoes')
    
    class Meta:
        # Garante que uma escalacao é única para cada confronto
        unique_together = ('confronto', )


class Substituicao(models.Model):
    confronto = models.ForeignKey(Confronto, on_delete=models.CASCADE)
    minuto = models.IntegerField()
    jogador_entrada = models.ForeignKey(Jogador, related_name='substituicoes_entrada', on_delete=models.CASCADE)
    jogador_saida = models.ForeignKey(Jogador, related_name='substituicoes_saida', on_delete=models.CASCADE)
    primeiro_tempo = models.BooleanField(default=False)

class Tipo_Lance(models.Model):
    tipo_lance = models.CharField(max_length=60)  # Usamos 'tipo_lance' para claridade

    def __str__(self):
        return self.tipo_lance
    

class Lance(models.Model):
    confronto = models.ForeignKey(Confronto, on_delete=models.CASCADE)
    minuto = models.IntegerField()
    jogador = models.ForeignKey(Jogador, on_delete=models.CASCADE)
    tipo_lance = models.ForeignKey(Tipo_Lance, on_delete=models.CASCADE, related_name='lances')
    link_video = models.URLField(blank=True, null=True)
    coordenadaX = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    coordenadaY = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    coordenadaXFinal = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    coordenadaYFinal = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    tempo = models.IntegerField(blank=True, null=True)
