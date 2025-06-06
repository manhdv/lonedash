from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .tasks import update_security_prices_for_user  # Bạn sẽ tạo hàm này

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    update_security_prices_for_user(user)
