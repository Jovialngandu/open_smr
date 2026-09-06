import random
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from api.models import (
    Asset,
    Evidence,
    IsoControl,
    Organization,
    Risk,
    Scope,
    SoaEntry,
    SoaVersion,
    SystemSetting,
    TreatmentTask,
    UserOrganizationRole,
    UserPreference,
    UserScopeAccess,
)

User = get_user_model()
fake = Faker('fr_FR')


class Command(BaseCommand):
    help = "Génère un jeu complet de données de démonstration pour tous les modèles."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Nombre d\'organisations à générer (défaut: 3).'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Purge les données métiers existantes avant de re-seeder.'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # 0. Réinitialisation si l'option --clear est passée
        if options['clear']:
            self.stdout.write(self.style.WARNING("[CLEAN] Purge des données métiers en cours..."))
            
            # Suppression des données générées (dans l'ordre pour respecter les ForeignKeys)
            Evidence.objects.all().delete()
            TreatmentTask.objects.all().delete()
            Risk.objects.all().delete()
            Asset.objects.all().delete()
            SoaVersion.objects.all().delete()
            SoaEntry.objects.all().delete()
            UserScopeAccess.objects.all().delete()
            Scope.objects.all().delete()
            UserOrganizationRole.objects.all().delete()
            UserPreference.objects.all().delete()
            Organization.objects.all().delete()
            
            # Suppression uniquement des utilisateurs de démo (conserve les superusers si nécessaire)
            User.objects.filter(is_superuser=False).delete()
            
            self.stdout.write(self.style.SUCCESS("✓ Purge terminée."))

        org_count = options['count']

        # Vérification du référentiel
        if not IsoControl.objects.exists():
            self.stderr.write(self.style.ERROR("Le référentiel ISO est vide. Lance 'python manage.py seed_iso_controls' d'abord."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("[RUN] Génération des données métier..."))

        # 1. Superutilisateur / Admin Global
        admin_user, _ = User.objects.get_or_create(
            username="admin_global",
            defaults={
                'email': "admin@opensmr.local",
                'first_name': "Super",
                'last_name': "Admin",
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password("Admin1234!")
        admin_user.save()

        # ... (reste du code inchangé)

        # 2. Paramètres Système
        SystemSetting.objects.update_or_create(
            key="MAX_ATTACHMENT_SIZE_MB",
            defaults={'value': {"size": 25}, 'description': "Taille max des pièces jointes de preuve"}
        )
        SystemSetting.objects.update_or_create(
            key="RISK_MATRIX_SCALE",
            defaults={'value': {"likelihood_max": 5, "impact_max": 5}, 'description': "Matrice d'évaluation des risques"}
        )

        # 3. Boucle Génération Organisations
        for _ in range(org_count):
            company_name = fake.company()
            org = Organization.objects.create(
                name=company_name,
                code=fake.unique.lexify(text="ORG-????").upper(),
                description=fake.catch_phrase()
            )

            # Création d'utilisateurs pour cette organisation
            roles_pool = ['ADMIN', 'RSSI', 'RISK_OWNER', 'AUDITOR']
            created_roles = []

            for role_type in roles_pool:
                user = User.objects.create_user(
                    username=fake.unique.user_name(),
                    email=fake.unique.company_email(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password="Password123!"
                )

                # Préférences Utilisateur
                UserPreference.objects.create(
                    user=user,
                    language=random.choice(['fr', 'en']),
                    theme=random.choice(['LIGHT', 'DARK', 'SYSTEM']),
                    email_notifications=True
                )

                # Rôle dans l'Organisation
                user_role = UserOrganizationRole.objects.create(
                    user=user,
                    organization=org,
                    role=role_type,
                    is_active=True
                )
                created_roles.append(user_role)

            # Création de Périmètres (Scopes)
            for i in range(random.randint(1, 2)):
                scope = Scope.objects.create(
                    organization=org,
                    name=f"Périmètre {fake.word().capitalize()} & {fake.job()}",
                    description=fake.text(max_nb_chars=150)
                )

                # Donner l'accès au Scope aux rôles de l'organisation
                for role in created_roles:
                    UserScopeAccess.objects.create(
                        user_organization_role=role,
                        scope=scope,
                        granted_by=admin_user
                    )

                # Personnaliser aléatoirement quelques SoA
                soa_entries = SoaEntry.objects.filter(scope=scope)
                for entry in soa_entries.order_by('?')[:15]:
                    entry.is_applicable = random.choice([True, True, False])
                    entry.implementation_status = random.choice(['NOT_IMPLEMENTED', 'IN_PROGRESS', 'IMPLEMENTED'])
                    entry.justification = fake.sentence()
                    entry.save()

                # Création d'Actifs (Assets)
                asset_categories = ['HARDWARE', 'SOFTWARE', 'DATA', 'PEOPLE', 'SERVICE', 'PHYSICAL']
                asset_owners = [r.user for r in created_roles]

                for _ in range(random.randint(3, 6)):
                    asset = Asset.objects.create(
                        scope=scope,
                        owner=random.choice(asset_owners),
                        name=f"{random.choice(['Serveur', 'Base', 'Service', 'Bureau'])} {fake.word().capitalize()}",
                        category=random.choice(asset_categories),
                        description=fake.text(max_nb_chars=100),
                        confidentiality=random.randint(1, 3),
                        integrity=random.randint(1, 3),
                        availability=random.randint(1, 3)
                    )

                    # Création de Risques sur l'Actif
                    for r_idx in range(random.randint(1, 3)):
                        risk = Risk.objects.create(
                            asset=asset,
                            code=fake.unique.lexify(text="RSK-???-###").upper(),
                            threat_description=f"Incapacité ou faille : {fake.sentence()}",
                            likelihood=random.randint(1, 5),
                            impact=random.randint(1, 5),
                            status=random.choice(['OPEN', 'IN_MITIGATION', 'ACCEPTED', 'CLOSED'])
                        )

                        # Tâches de traitement de risque
                        if risk.status in ['IN_MITIGATION', 'CLOSED']:
                            target_soa = soa_entries.order_by('?').first()
                            
                            if target_soa:
                                is_closed = (risk.status == 'CLOSED')
                                task_status = 'COMPLETED' if is_closed else random.choice(['TODO', 'IN_PROGRESS'])

                                TreatmentTask.objects.create(
                                    risk=risk,
                                    iso_control=target_soa.iso_control,
                                    assignee=random.choice(asset_owners),
                                    title=f"Mesure corrective : {fake.catch_phrase()}",
                                    description=fake.text(max_nb_chars=120),
                                    due_date=fake.future_date(),
                                    status=task_status,
                                    completed_at=timezone.now() if task_status == 'COMPLETED' else None
                                )

        self.stdout.write(self.style.SUCCESS(
            "✓ Base de données alimentée avec succès !"
        ))