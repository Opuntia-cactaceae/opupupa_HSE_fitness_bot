
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = '53da5167f76a'
down_revision: Union[str, Sequence[str], None] = '7b97fd011774'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE water_logs SET id = nextval('water_logs_id_seq') WHERE id = 0")
    op.execute("SELECT setval('water_logs_id_seq', (SELECT MAX(id) FROM water_logs), true)")

                 
    op.execute("UPDATE daily_stats SET id = nextval('daily_stats_id_seq') WHERE id = 0")
    op.execute("SELECT setval('daily_stats_id_seq', (SELECT MAX(id) FROM daily_stats), true)")

                  
    op.execute("UPDATE workout_logs SET id = nextval('workout_logs_id_seq') WHERE id = 0")
    op.execute("SELECT setval('workout_logs_id_seq', (SELECT MAX(id) FROM workout_logs), true)")


def downgrade() -> None:
    
    pass
