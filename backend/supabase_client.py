import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[WARNING] Supabase credentials missing in .env file (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")
        return None
    
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception as e:
        print(f"[ERROR] Failed to initialize Supabase client: {e}")
        return None
