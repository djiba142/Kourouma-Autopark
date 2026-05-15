from django.db import models
from django.conf import settings

class LoginLog(models.Model):
    """Log de chaque tentative de connexion."""
    utilisateur   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='login_logs',
    )
    email_tente   = models.EmailField(default='')
    succes        = models.BooleanField(default=False)
    ip            = models.GenericIPAddressField(null=True, blank=True)
    user_agent    = models.CharField(max_length=300, default='')
    date          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Log Connexion'

    def __str__(self):
        statut = '✓' if self.succes else '✗'
        return f'{statut} {self.email_tente} — {self.ip} — {self.date}'

    @property
    def device_court(self):
        ua = self.user_agent.lower()
        if 'mobile' in ua or 'android' in ua:    return '📱 Mobile'
        if 'tablet' in ua or 'ipad' in ua:        return '📟 Tablette'
        if 'windows' in ua:                        return '🖥️ Windows'
        if 'mac' in ua:                            return '🍎 Mac'
        if 'linux' in ua:                          return '🐧 Linux'
        return '💻 Navigateur'


class SettingDynamique(models.Model):
    """
    Stockage clé-valeur pour les paramètres configurables via l'interface.
    Ex: objectif_ventes_mensuel
    """
    cle    = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()

    def __str__(self):
        return f"{self.cle} = {self.valeur}"
