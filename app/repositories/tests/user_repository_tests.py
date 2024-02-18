# """CRUD functions for users table"""
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from app.core.memory_db import USERS
# from app.core.database import test_db
# import schemas
# from repositories import user_repository



# from app.models.user_model import DBUser



# TESTS
# import test_db ie; from app.core.database import test_db
# and use it directly as the db variable ie; db=test_db
    
# try:
#     test_create_user = schemas.CreateUserHashed(
#         email="youremail@email.com",
#         hashed_password="fakehashedsecrethashed"
#     )
#     user_repository.create_user(db=test_db, user=test_create_user)
#     test_db_user = user_repository.get_user_by_email(db=test_db, email="myemail@email.com")
#     print(test_db_user)
# except IntegrityError as e:
#     print(e.orig)
    
# finally:
#     test_db.close()


