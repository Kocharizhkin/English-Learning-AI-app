from sqlalchemy import Column, Integer, String, DateTime, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

DATABASE_URL = "***"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    phrase = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    image = Column(String, nullable=True)
    date_added = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    async def get_session():
        return AsyncSessionLocal()

    async def add_entry(self, session: AsyncSession, user_id: int, phrase: str, translation: str, image: str):
        async with session.begin():
            stmt = select(func.max(Vocabulary.id))
            result = await session.execute(stmt)
            latest_id = result.scalar()

            # If there are no users in the db, latest_id will be None.
            # In that case, start with id 1, otherwise increment latest_id by 1.
            new_id = 1 if latest_id is None else latest_id + 1

            entry = Vocabulary(id = new_id, user_id=user_id, phrase=phrase, translation=translation, image=image, date_added = datetime.now().date())
            session.add(entry)
            return await entry.to_dict()

    @classmethod
    async def get_entries_by_user_id(cls, session: AsyncSession, user_id: int):
        async with session.begin():
            stmt = select(Vocabulary).where(Vocabulary.user_id == user_id).order_by(Vocabulary.date_added.desc())
            result = await session.execute(stmt)
            return [await entry.to_dict() for entry in result.scalars()]

    @classmethod
    async def delete_entry(cls, session: AsyncSession, entry_id: int):
        async with session.begin():
            stmt = select(Vocabulary).where(Vocabulary.id == entry_id)
            result = await session.execute(stmt)
            entry = result.scalar()

            if entry:
                await session.delete(entry)
                await session.commit()
                return True
            return False

    async def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phrase': self.phrase,
            'translation': self.translation,
            'image': self.image,
            'date_added': self.date_added.strftime('%Y-%m-%d')
        }






    