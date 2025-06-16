from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dash.models import TradeEntry
from dash.utils import utils_recalc_daily_holdings  # sửa lại path nếu khác


class Command(BaseCommand):
    help = "Recalculate all historical daily holdings for all users"

    def handle(self, *args, **options):
        entries = TradeEntry.objects.select_related("security", "user").order_by("date")
        seen = set()

        for entry in entries:
            key = (entry.user, entry.security)
            if key in seen:
                continue

            seen.add(key)
            utils_recalc_daily_holdings(entry.user, entry.security, entry.date)

        self.stdout.write(self.style.SUCCESS("Recalculation completed."))

