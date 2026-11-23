"""Création initiale des tables Squadra 8.

Cette première révision applique les métadonnées validées des modèles. Les révisions
suivantes générées par Alembic décriront les évolutions table par table.
"""

from alembic import op

from app.db.models import Base

revision = "20261123_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
