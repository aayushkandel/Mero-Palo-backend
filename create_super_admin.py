import getpass
from src.utils.db import LocalSession
from src.users.models import User



db = LocalSession()


email = input("Enter email: ")
password = getpass.getpass("Enter password: ")

user = User(
   
    email=email,
    password=(password),
    role="super_admin"
)

db.add(user)
db.commit()

print("Super admin created successfully.")

db.close()