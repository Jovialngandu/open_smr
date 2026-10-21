import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_organizationinvitation_role"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatConversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("title", models.CharField(blank=True, default="Nouvelle conversation", max_length=200)),
                ("is_archived", models.BooleanField(db_index=True, default=False)),
                ("last_activity", models.DateTimeField(auto_now=True, db_index=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-last_activity", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="chatconversation",
            index=models.Index(fields=["user", "-last_activity"], name="api_chatconv_user_last_a_idx"),
        ),
        migrations.AddIndex(
            model_name="chatconversation",
            index=models.Index(fields=["user", "is_archived", "-last_activity"], name="api_chatconv_user_arch_last_a_idx"),
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("role", models.CharField(choices=[("user", "user"), ("assistant", "assistant")], db_index=True, max_length=20)),
                ("content", models.TextField()),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="api.chatconversation")),
            ],
            options={
                "ordering": ["created_at", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["conversation", "created_at"], name="api_chatmess_conversat_idx"),
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(fields=["conversation", "role", "created_at"], name="api_chatmess_conversat_role_idx"),
        ),
    ]
