import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types
from supabase import create_client, Client

# 環境変数の読み込み（または適宜設定）
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)


def evaluate_articles_with_gemini(
    articles: List[Dict[str, Any]],
    user_context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Gemini APIに記事リストを渡し、一括でスコアと一言コメントをJSON形式で生成させる。
    """
    if not articles:
        return []

    # Geminiに渡すための軽量なデータ構造に整形
    articles_payload = [
        {
            "id": article["id"],
            "title": article["title"],
            "summary": article.get("ai_comment", "") or article.get("summary", "")[:300]
        }
        for article in articles
    ]

    system_instruction = f"""
あなたは、技術情報をユーザーの目標や関心に照らして整理するリサーチメンターです。
記事をユーザーの開発タスクに無理に結びつけず、情報共有や長期的な学びとして価値がある場合も適切に評価してください。
新しさだけで価値を判断せず、記事内容がユーザーのコンテクストにどう関係するかを根拠にしてください。
不安をあおったり、記事だけからキャリアの将来を断定したりしないでください。

【ユーザーのコンテクスト】
{json.dumps(user_context, ensure_ascii=False)}

【出力要件】
各記事の `id` に対し、コンテクストとの関連度を `score`（0〜100の整数）、なぜ関係があるかを簡潔に表す `comment`（1〜2文）を付けてください。
根拠が薄い記事に無理な関連づけをせず、低いスコアにしてください。
必ず有効なJSON配列だけを返してください。形式は [{{"id": 1, "score": 0, "comment": "..."}}] です。
"""

    user_prompt = f"""
以下の未読RSSニュース一覧を評価し、指定されたJSON構造で返してください。

ニュース一覧:
{json.dumps(articles_payload, ensure_ascii=False)}
"""
    try:
        # 構造化出力（JSON Mode）を指定してGeminiを呼び出し
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2, # 揺らぎを少なくして一貫した評価をさせる
            ),
        )
        
        result_data = json.loads(response.text)
        return result_data
    except Exception as e:
        print(f"Gemini APIによる評価処理でエラーが発生しました: {e}")
        return []


