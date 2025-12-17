from passlib.context import CryptContext

try:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    hash = pwd_context.hash("password123")
    print(f"Success: {hash}")
except Exception as e:
    print(f"Error: {e}")
