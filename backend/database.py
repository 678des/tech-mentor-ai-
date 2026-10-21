import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabaseクライアントのインスタンスを生成してエクスポート
print("取得したURL"+str(SUPABASE_URL))
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)