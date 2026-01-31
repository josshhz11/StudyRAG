from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

print("Testing Supabase connection...")
print(f"URL: {url}")
print(f"Key: {key[:20]}..." if key else "Key: Not found")

if not url or not key:
    print("\n❌ Missing Supabase credentials in .env file!")
    print("\nAdd these to your .env:")
    print("SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co")
    print("SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    exit(1)

try:
    supabase = create_client(url, key)
    print("\n✅ Supabase connection successful!")
    
    # Test signup
    print("\n📝 Testing user signup...")
    try:
        response = supabase.auth.sign_up({
            "email": "test@example.com",
            "password": "TestPassword123!",
            "options": {
                "data": {
                    "username": "testuser"
                }
            }
        })
        if response.user:
            print(f"✅ Test signup successful!")
            print(f"   User ID: {response.user.id}")
            print(f"   Email: {response.user.email}")
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg or "already been registered" in error_msg:
            print("✅ User already exists (that's fine!)")
        else:
            print(f"⚠️  Signup error: {e}")
    
    # Test login
    print("\n🔐 Testing user login...")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        if response.session:
            print("✅ Test login successful!")
            print(f"   User ID: {response.user.id}")
            print(f"   Session token: {response.session.access_token[:30]}...")
            print(f"   Token expires at: {response.session.expires_at}")
        else:
            print("❌ Login failed: No session returned")
    except Exception as e:
        print(f"❌ Login failed: {e}")
    
    print("\n" + "="*60)
    print("🎉 All tests passed! Supabase is ready to use.")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check your SUPABASE_URL and SUPABASE_ANON_KEY in .env")
    print("2. Make sure your Supabase project is created")
    print("3. Verify the credentials from Settings > API in Supabase dashboard")
