from allauth.account.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def fetch_api_data_on_login(sender, request, user, **kwargs):
    fetch_api_data(user)