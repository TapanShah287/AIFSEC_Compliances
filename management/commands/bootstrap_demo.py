# management/commands/bootstrap_demo.py
import os, json
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = "Load demo fixtures and print next steps."

    def add_arguments(self, parser):
        parser.add_argument("--fixtures-dir", default="fixtures", help="Directory containing seed_*.json")

    def handle(self, *args, **opts):
        fixtures_dir = opts["fixtures_dir"]
        seeds = ["seed_investors.json","seed_companies.json","seed_funds.json","seed_transactions.json"]
        for seed in seeds:
            path = os.path.join(fixtures_dir, seed)
            if not os.path.exists(path):
                self.stdout.write(self.style.WARNING(f"Missing: {path} (skipping)"))
                continue
            self.stdout.write(f"Loading {path} ...")
            call_command("loaddata", path)
        self.stdout.write(self.style.SUCCESS("Demo bootstrap complete."))
        self.stdout.write("Visit /admin and /api/ to verify.")