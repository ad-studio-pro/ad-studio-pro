"""
Generate a bcrypt hash for a password — paste output into auth_config.yaml.

Usage:
    python scripts/auth_make_hash.py YourPasswordHere
"""

import sys

try:
    import streamlit_authenticator as stauth
except ImportError:
    print("streamlit-authenticator not installed. Run: pip install streamlit-authenticator")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python scripts/auth_make_hash.py <password>")
    sys.exit(1)

password = sys.argv[1]
hashed = stauth.Hasher([password]).generate()[0]
print(f"\nPassword: {password}")
print(f"Hash:     {hashed}")
print(f"\nPaste the hash (the whole line starting with $2b$) into auth_config.yaml")
