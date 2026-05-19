from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash = "$2b$12$BFOuzH0mFcfQSGs8pod7tuUzm.P4kkHGDvEX1J2fdZtHHgYN0ykOG"
password = "Admin123*"

print(f"MATCH: {pwd_context.verify(password, hash)}")
