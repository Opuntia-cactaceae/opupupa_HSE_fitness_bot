
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


                                        
revision: str = '9da5e8a5ae98'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('food_logs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('logged_at', sa.DateTime(), nullable=False),
    sa.Column('product_query', sa.Text(), nullable=False),
    sa.Column('product_name', sa.Text(), nullable=False),
    sa.Column('source', sa.Text(), nullable=False),
    sa.Column('product_external_id', sa.Text(), nullable=True),
    sa.Column('kcal_per_100g', sa.Float(), nullable=False),
    sa.Column('grams', sa.Float(), nullable=False),
    sa.Column('kcal_total', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('daily_stats',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('temperature_c', sa.Float(), nullable=True),
    sa.Column('water_goal_ml', sa.Integer(), nullable=False),
    sa.Column('calorie_goal_kcal', sa.Integer(), nullable=False),
    sa.Column('water_logged_ml', sa.Integer(), nullable=False),
    sa.Column('calories_consumed_kcal', sa.Integer(), nullable=False),
    sa.Column('calories_burned_kcal', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='public'
    )
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('weight_kg', sa.Float(), nullable=False),
    sa.Column('height_cm', sa.Float(), nullable=False),
    sa.Column('age_years', sa.Integer(), nullable=False),
    sa.Column('sex', sa.Text(), nullable=True),
    sa.Column('activity_minutes_per_day', sa.Integer(), nullable=False),
    sa.Column('city', sa.Text(), nullable=False),
    sa.Column('timezone', sa.Text(), nullable=False),
    sa.Column('calorie_goal_mode', sa.Text(), nullable=False),
    sa.Column('calorie_goal_kcal_manual', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('water_logs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('logged_at', sa.DateTime(), nullable=False),
    sa.Column('ml', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('workout_logs',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('logged_at', sa.DateTime(), nullable=False),
    sa.Column('workout_type', sa.Text(), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.Column('kcal_burned', sa.Float(), nullable=False),
    sa.Column('water_bonus_ml', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
                                  


def downgrade() -> None:
    op.drop_table('workout_logs')
    op.drop_table('water_logs')
    op.drop_table('users')
    op.drop_table('daily_stats', schema='public')
    op.drop_table('food_logs')
                                  
