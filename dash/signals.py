from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import AccountBalance
from .utils import utils_update_security_prices_for_user, utils_recalc_portfolio, utils_update_account
from datetime import date as date_dt

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    utils_update_security_prices_for_user(user)

#def _affected_accounts_and_date(instance):
#    if isinstance(instance, (TradeEntry, TradeExit, Transaction)):
#        return {instance.account}, instance.date
#    if isinstance(instance, SecurityPrice):
#        entries = TradeEntry.objects.filter(security=instance.security).select_related('account')
#        accounts = set(e.account for e in entries)
#        return accounts, instance.date
#    return set(), None


#@receiver([post_save, post_delete], sender=TradeEntry)
#@receiver([post_save, post_delete], sender=TradeExit)
#@receiver([post_save, post_delete], sender=Transaction)
#@receiver([post_save, post_delete], sender=SecurityPrice)
#def auto_utils_update_account(sender, instance, **kwargs):
#    accounts, start_date = _affected_accounts_and_date(instance)
#    for acc in accounts:
#        # Skip if account is being (or has been) deleted
#        if acc is None:
#            continue
#        print(f"DEBUG utils_update_account called with account={acc} (id={acc.id}) and start_date={start_date}")
#
#        utils_update_account(acc, start_date=start_date)

@receiver([post_save, post_delete], sender=AccountBalance)
def sync_portfolio_on_balance_change(sender, instance, **kwargs):
    """Whenever a balance row changes → refresh that day’s portfolio total."""
    utils_recalc_portfolio(instance.account.user, instance.date)
