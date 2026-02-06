
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = '7b97fd011774'
down_revision: Union[str, Sequence[str], None] = '9da5e8a5ae98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "water_goal_mode",
            sa.Text(),
            nullable=False,
            server_default="auto",
        ),
    )

                                        
    op.add_column(
        "users",
        sa.Column("water_goal_ml_manual", sa.Integer(), nullable=True),
    )

                                                                                           
    op.alter_column("users", "water_goal_mode", server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'water_goal_ml_manual')
    op.drop_column('users', 'water_goal_mode')
                                  
