"""Création initiale des tables Squadra 8 (op.create_table explicites)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261123_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "produit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("nom", sa.String(), nullable=False),
        sa.Column("nom_fpma", sa.String(), nullable=True),
        sa.Column("touche", sa.Integer(), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.CheckConstraint("touche BETWEEN 1 AND 9", name="ck_produit_touche"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("touche", name="uq_produit_touche"),
    )

    op.create_table(
        "marche",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("nom", sa.String(), nullable=False),
        sa.Column("commune", sa.String(), nullable=False),
        sa.Column("nom_fpma", sa.String(), nullable=True),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("nom", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("licence", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("nom_affiche", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("mot_de_passe_hash", sa.String(length=255), nullable=False),
        sa.Column("actif", sa.Boolean(), nullable=False),
        sa.Column(
            "cree_le",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'validateur', 'saisie')",
            name="ck_utilisateur_role",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "prix",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("produit_id", sa.Integer(), nullable=False),
        sa.Column("marche_id", sa.Integer(), nullable=False),
        sa.Column("prix_fcfa", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unite", sa.String(), nullable=False),
        sa.Column("type_prix", sa.String(), nullable=False),
        sa.Column("date_releve", sa.Date(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(), nullable=False),
        sa.Column("score_anomalie", sa.Float(), nullable=True),
        sa.Column("motif_anomalie", sa.Text(), nullable=True),
        sa.Column("saisi_par", sa.Integer(), nullable=True),
        sa.Column("valide_par", sa.Integer(), nullable=True),
        sa.Column("date_validation", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motif_rejet", sa.Text(), nullable=True),
        sa.Column(
            "cree_le",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("prix_fcfa > 0", name="ck_prix_positif"),
        sa.CheckConstraint("unite IN ('kg', 'sac_100kg')", name="ck_prix_unite"),
        sa.CheckConstraint("type_prix IN ('detail', 'gros')", name="ck_prix_type"),
        sa.CheckConstraint(
            "statut IN ('en_attente', 'valide', 'rejete')",
            name="ck_prix_statut",
        ),
        sa.ForeignKeyConstraint(["produit_id"], ["produit.id"]),
        sa.ForeignKeyConstraint(["marche_id"], ["marche.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"]),
        sa.ForeignKeyConstraint(["saisi_par"], ["utilisateur.id"]),
        sa.ForeignKeyConstraint(["valide_par"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "produit_id",
            "marche_id",
            "date_releve",
            "type_prix",
            "source_id",
            name="uq_prix_observation",
        ),
    )

    op.create_table(
        "appel",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("numero_hash", sa.CHAR(length=64), nullable=True),
        sa.Column("canal", sa.String(), nullable=False),
        sa.Column(
            "debut",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("produit_id", sa.Integer(), nullable=True),
        sa.Column("nb_actions", sa.Integer(), nullable=False),
        sa.Column("demande_humain", sa.Boolean(), nullable=False),
        sa.Column("statut", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["produit_id"], ["produit.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "interaction",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("appel_id", sa.Uuid(), nullable=False),
        sa.Column("etape", sa.String(), nullable=False),
        sa.Column("entree", sa.String(), nullable=False),
        sa.Column("texte_transcrit", sa.Text(), nullable=True),
        sa.Column("intention", sa.String(), nullable=True),
        sa.Column("methode", sa.String(), nullable=True),
        sa.Column("latence_ms", sa.Integer(), nullable=True),
        sa.Column(
            "horodatage",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["appel_id"], ["appel.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "demande_rappel",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("numero_chiffre", sa.Text(), nullable=True),
        sa.Column("numero_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("motif", sa.String(), nullable=False),
        sa.Column(
            "cree_le",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("rappel_prevu_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("statut", sa.String(), nullable=False),
        sa.Column("efface_le", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_demande_rappel_numero_hash",
        "demande_rappel",
        ["numero_hash"],
        unique=False,
    )

    op.create_table(
        "liste_noire",
        sa.Column("numero_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("raison", sa.Text(), nullable=False),
        sa.Column("jusqu_au", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("numero_hash"),
    )

    op.create_table(
        "journal",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("utilisateur_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("cible", sa.String(), nullable=False),
        sa.Column(
            "quand",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("journal")
    op.drop_table("liste_noire")
    op.drop_index("ix_demande_rappel_numero_hash", table_name="demande_rappel")
    op.drop_table("demande_rappel")
    op.drop_table("interaction")
    op.drop_table("appel")
    op.drop_table("prix")
    op.drop_table("utilisateur")
    op.drop_table("source")
    op.drop_table("marche")
    op.drop_table("produit")
