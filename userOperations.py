from sqlalchemy import Column, Integer, String, select, update, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://ege_bot:ege_bot@localhost/ege_bot"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    level = Column(Integer, default=0)
    last_lesson_id = Column(Integer, default=0)
    fullname = Column(String(255))
    username = Column(String(255), unique=True)
    profilepicurl = Column(String(1000))
    translates_count = Column(Integer, default=0)

    @staticmethod
    async def get_session():
        return AsyncSessionLocal()

    async def add_user(self, session: AsyncSession, user: 'User'):
        async with session.begin():
            # Query to get the highest user id from the database
            stmt = select(func.max(User.id))
            result = await session.execute(stmt)
            latest_id = result.scalar()

            # If there are no users in the db, latest_id will be None.
            # In that case, start with id 1, otherwise increment latest_id by 1.
            new_id = 1 if latest_id is None else latest_id + 1

            # Assign the new id to the user object
            user.id = new_id

            # Add the new user to the session
            session.add(user)

    @classmethod
    async def get_user_by_id(cls, session: AsyncSession, user_id: int) -> 'User':
        async with session.begin():
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()
        
    @classmethod
    async def check_credentials(cls, session: AsyncSession, email: str, hashed_password: str) -> bool:
        async with session.begin():
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user is None:
                return False  # User not found
            
            return user.password == hashed_password, user

    async def get_user_data(self, id=0):
        if update.message:
            user = update.message.from_user
        elif update.callback_query:
            user = update.callback_query.from_user
        elif update.poll_answer:
            user = update.poll_answer.user
        async with AsyncSessionLocal() as session:
            user_info = await self.get_user_by_id(session, user['id'])
        if user_info is None:
            new_user = User(
                id=user['id'],
                username=user['username'],
                fullname=user['fullname'],
                profilepicurl="",  # Placeholder, update if you have the data
                level=0,
                last_lesson_id=0,
            )
            async with AsyncSessionLocal() as session:
                await self.add_user(session, new_user)
            user_info = new_user
        return user_info

    async def update_user(self, updated_user, reset=False):
        async with AsyncSessionLocal() as session:
            # Get the existing user object from the database
            existing_user = await self.get_user_by_id(session, updated_user.id)
            
            if not existing_user:
                # Handle the case where the user does not exist in the database
                print(f"No user found with id={updated_user.id}")
                return
            
            # Dictionary to hold the fields to be updated
            fields_to_update = {}
            
            # List of fields to compare and possibly update.
            # These should be the fields that could have differences
            fields = [
                'level', 
                'last_lesson_id',
                'fullname',
                'username',
                'profilepicurl',
                'translates_count'   
            ]
            
            initial_values = {
                'level': 0,
                'last_lesson_id': 0,
            }

            for field in fields:
                if reset:
                    # Reset the field to its initial value
                    fields_to_update[field] = initial_values[field]
                else:
                    existing_value = getattr(existing_user, field)
                    updated_value = getattr(updated_user, field)

                    if existing_value != updated_value:
                        fields_to_update[field] = updated_value
                    
            if fields_to_update:
                # If there are differences, then perform the update
                stmt = (
                    update(User)
                    .where(User.id == updated_user.id)
                    .values(**fields_to_update)
                )
                await session.execute(stmt)
                await session.commit()

    async def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'fullname': self.fullname,
            'username': self.username,
            'profilepicurl': self.profilepicurl,
            'level': self.level,
            'last_lesson_id': self.last_lesson_id,
            'translates_count': self.translates_count  # Include the new column in the to_dict method
        }