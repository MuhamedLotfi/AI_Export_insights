from backend.ai_agent.auth_service import AuthService
from backend.ai_agent.data_adapter import get_adapter
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_auth():
    print("--- Debugging Auth ---")
    
    # 1. Initialize Service
    auth_service = AuthService()
    adapter = get_adapter()
    
    # 2. Get User
    username = "admin"
    password_attempt = "admin123"
    
    print(f"Fetching user: {username}")
    users = adapter.query("users", {"username": username})
    if not users:
        print("User not found!")
        return

    user = users[0]
    stored_hash = user.get("password_hash", "")
    print(f"Stored Hash: {stored_hash}")
    
    # 3. Verify using AuthService (which uses its own CryptContext)
    print(f"Attempting to verify '{password_attempt}'...")
    is_valid = auth_service.verify_password(password_attempt, stored_hash)
    print(f"AuthService.verify_password result: {is_valid}")
    
    # 4. If invalid, try to generate a new one and verify it immediately
    if not is_valid:
        print("Verification failed. Generating new hash...")
        new_hash = auth_service.hash_password(password_attempt)
        print(f"New Hash: {new_hash}")
        
        # Verify the new hash immediately
        is_valid_new = auth_service.verify_password(password_attempt, new_hash)
        print(f"Verification of NEW hash result: {is_valid_new}")
        
        if is_valid_new:
            print("New hash works. Updating database...")
            adapter.update("users", user["id"], {"password_hash": new_hash})
            print("Database updated!")
        else:
            print("CRITICIAL: Even the new hash could not be verified. usage of bcrypt/passlib might be broken.")
    else:
        print("Verification SUCCESS. The password should work.")

if __name__ == "__main__":
    debug_auth()
