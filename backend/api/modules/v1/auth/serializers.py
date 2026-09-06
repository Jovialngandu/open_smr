from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from api.models import UserOrganizationRole, UserScopeAccess
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

def build_jwt_payload_for_user(user, organization_id=None, scope_id=None):
    """
    Génère un RefreshToken en injectant le contexte organisationnel/scope.
    Gère proprement les cas :
    - Sans Organisation (org_id: null, scope_id: null)
    - Avec Organisation mais Sans Scope (org_id: UUID, scope_id: null)
    - Avec Organisation et Avec Scope (org_id: UUID, scope_id: UUID)
    """
    token = RefreshToken.for_user(user)

    if not user.is_active:
        raise serializers.ValidationError("Ce compte utilisateur est désactivé.")

    token['username'] = user.username
    token['email'] = user.email
    token['is_superuser'] = user.is_superuser

    # 1. Récupération des rôles organisationnels actifs
    roles_qs = UserOrganizationRole.objects.filter(user=user, is_active=True)

    active_role = None
    if roles_qs.exists():
        if organization_id:
            active_role = roles_qs.filter(organization_id=organization_id).first()
            if not active_role and not user.is_superuser:
                raise serializers.ValidationError("Vous n'avez pas de rôle actif dans cette organisation.")
        else:
            # Sélection par défaut du premier rôle organisationnel
            active_role = roles_qs.first()

    # 2. Assignation des claims selon le rôle organisationnel trouvé
    if active_role:
        token['organization_id'] = str(active_role.organization_id)
        token['role'] = active_role.role

        # Recherche des périmètres (Scopes) rattachés à ce rôle
        scopes_qs = UserScopeAccess.objects.filter(user_organization_role=active_role)
        
        if scope_id:
            valid_scope = scopes_qs.filter(scope_id=scope_id).first()
            if not valid_scope and not user.is_superuser:
                raise serializers.ValidationError("Accès non autorisé à ce périmètre (Scope).")
            token['scope_id'] = str(scope_id)
        else:
            # S'il a des scopes, on prend le premier, SINON on laisse à None sans lever d'erreur
            first_scope = scopes_qs.first()
            token['scope_id'] = str(first_scope.scope_id) if first_scope else None
    else:
        # Cas où l'utilisateur n'a aucune organisation
        token['organization_id'] = None
        token['role'] = None
        token['scope_id'] = None

    return token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Permet la connexion JWT même si l'utilisateur n'a pas d'organisation."""
    organization_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)
    scope_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    def validate(self, attrs):
        data = super().validate(attrs)
        org_id = attrs.get('organization_id')
        scope_id = attrs.get('scope_id')

        refresh = build_jwt_payload_for_user(self.user, organization_id=org_id, scope_id=scope_id)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data


class SwitchContextSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=True)
    scope_id = serializers.UUIDField(required=False, allow_null=True)


class UserProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'roles']

    def get_roles(self, obj):
        roles = UserOrganizationRole.objects.filter(user=obj, is_active=True)
        return [
            {
                'organization_id': str(r.organization_id),
                'organization_name': r.organization.name,
                'role': r.role
            }
            for r in roles
        ]
        
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    
    # Champ optionnel si l'utilisateur veut directement créer sa structure/organisation à l'inscription
    organization_name = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)


class RegisterResponseSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    access = serializers.CharField()
    refresh = serializers.CharField()