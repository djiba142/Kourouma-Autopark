from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, nom, password=None, role='EMPLOYE', **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, nom=nom, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nom, password, role='ADMIN', **extra_fields)

class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('ADMIN', 'Administrateur'),
        ('EMPLOYE', 'Employé'),
        ('MAGASINIER', 'Magasinier'),
    )

    email = models.EmailField(unique=True, verbose_name="Adresse email")
    nom = models.CharField(max_length=100, verbose_name="Nom complet")
    role = models.CharField(max_length=15, choices=ROLES, default='EMPLOYE')
    actif = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)
    
    # Security tracking
    tentatives_echouees = models.PositiveIntegerField(default=0)
    derniere_tentative = models.DateTimeField(null=True, blank=True)
    
    # Required for Django Admin
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True) # Used by Django's auth system

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.nom} ({self.role})"
