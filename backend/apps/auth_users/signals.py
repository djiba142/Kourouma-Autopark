from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from audit.models import LogActivite

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Signal envoyé lorsqu'un token de réinitialisation est créé.
    Gère l'envoi de l'email réel avec le logo BSG.
    """
    # Dans une app réelle, l'URL pointerait vers votre frontend mobile/web
    context = {
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.nom,
        'email': reset_password_token.user.email,
        'reset_password_url': "{}?token={}".format(
            instance.request.build_absolute_uri(reverse('password_reset:reset-password-confirm')),
            reset_password_token.key
        ),
        'token': reset_password_token.key
    }

    # Rendu du template HTML (Prévu pour BSG Auto)
    email_html_message = render_to_string('email/user_reset_password.html', context)
    email_plaintext_message = render_to_string('email/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Réinitialisation de mot de passe - BSG Auto Parts",
        # message:
        email_plaintext_message,
        # from:
        "noreply@bsgautopieces.com",
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()

    # Log de l'audit
    LogActivite.objects.create(
        utilisateur=reset_password_token.user,
        action="DEMANDE_RESET_PASSWORD",
        details=f"Email de récupération envoyé à {reset_password_token.user.email}"
    )
