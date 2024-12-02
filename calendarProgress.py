from sqlalchemy import Column, Integer, String, DateTime, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

DATABASE_URL = "***"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

class ProgressInCalendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=False)
    translates_count = Column(Integer)

    @staticmethod
    async def get_session():
        return AsyncSessionLocal()

    @classmethod
    async def add(cls, session, user_id, translates_count):
        async with session.begin():
            new_entry = cls(user_id=user_id, translates_count=translates_count)
            session.add(new_entry)
            return new_entry

    @classmethod
    async def get(cls, session, user_id):
        async with session.begin():
            result = await session.execute(
                select(cls)
                .where(cls.user_id == user_id)
                .order_by(cls.date.desc())
            )
            results = result.scalars().all()
            return [await item.to_dict() for item in results]
        
    async def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'translates_count': self.translates_count,
        }