from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    weight_kg: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)
    age_years: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_minutes_per_day: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str] = mapped_column(Text, default="")
    timezone: Mapped[str] = mapped_column(Text, default="Europe/Amsterdam")
    calorie_goal_mode: Mapped[str] = mapped_column(Text, default="auto")
    calorie_goal_kcal_manual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_goal_mode: Mapped[str] = mapped_column(Text, default="auto")
    water_goal_ml_manual: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DailyStatsModel(Base):
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_goal_ml: Mapped[int] = mapped_column(Integer, default=0)
    calorie_goal_kcal: Mapped[int] = mapped_column(Integer, default=0)
    water_logged_ml: Mapped[int] = mapped_column(Integer, default=0)
    calories_consumed_kcal: Mapped[int] = mapped_column(Integer, default=0)
    calories_burned_kcal: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = ({"schema": "public"},)


class FoodLogModel(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    product_query: Mapped[str] = mapped_column(Text)
    product_name: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    product_external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    kcal_per_100g: Mapped[float] = mapped_column(Float, default=0.0)
    grams: Mapped[float] = mapped_column(Float, default=0.0)
    kcal_total: Mapped[float] = mapped_column(Float, default=0.0)


class WorkoutLogModel(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    workout_type: Mapped[str] = mapped_column(Text)
    minutes: Mapped[int] = mapped_column(Integer)
    kcal_burned: Mapped[float] = mapped_column(Float, default=0.0)
    water_bonus_ml: Mapped[int] = mapped_column(Integer, default=0)


class WaterLogModel(Base):
    __tablename__ = "water_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ml: Mapped[int] = mapped_column(Integer)