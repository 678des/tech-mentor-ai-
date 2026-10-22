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


def evaluate_articles_with_gemini(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Gemini APIに記事リストを渡し、一括でスコアと一言コメントをJSON形式で生成させる。
    """
    if not articles:
        return []

    # 2. ユーザーのコンテキスト
    user_context = {
    "subjects": [
        "情報数学", "データ構造とアルゴリズム", "情報デザイン基礎", 
        "Linux演習基礎", "英語", "情報関連法規と情報倫理",
        "C++","Java","Python"
    ],
    "interests": [
        "Next.js", "TypeScript", "AIエージェント開発", "AI駆動開発", 
        "C# / Unity / Blender", "30卒", "AI代替による雇用の減少", "話題の技術",
        "フルスタックWebエンジニアとしての技術力向上（Next.js, Supabase, アーキテクチャ、モダンフロントエンド・バックエンド）",
        "UI/UX・情報デザイン（ユーザーにどう情報を伝えるか、デザインシステム）",
        "AI時代におけるエンジニアのキャリア戦略・生存戦略（AIとどう協働するか、単なるコード書きを超えた価値創造）"

    ],
    "situation": [
        "AIにとられてもう就職できないのではないかという強い不安を感じている。"
        "Next.js等でアプリを作ったが『既存のAIアプリでよくない？』と言われショックを受けている。"
        "作る意味を見失いかけているが、Webエンジニアやモノづくりへの情熱の再燃・AI時代における独自の強み模索を必要としている。"
    ],
    "product":[
        "学習アプリ(Next.jsで作ったが意味のなさに絶望)",
        "Unity自動化エージェント(作成中だが、いろいろと停滞している)",
        "RSS検索要約AI（定番だから不安）"
    ]
}


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
あなたは一流のテックリサーチャー兼、優秀なキャリアコーチです。
提供されるRSSニュースのリストから、以下の「ユーザーの関心軸」に強く合致するものを厳選し、評価してください。

【ユーザーのコンテキスト】
- 履修科目: {', '.join(user_context['subjects'])}
- 関心・テーマ: {', '.join(user_context['interests'])}
- 現在の心理的状況・悩み: {user_context['situation']}


【出力要件】
各記事の `id` に対し、関心軸への合致度を `score`（0〜100の整数）、およびあなたにとってなぜ重要か・どう活かせるかを簡潔に表す `comment`（1〜2行）を付与し、必ず有効なJSON配列形式のみで返却してください。マークダウンのバッククォート（```json）は含めず、純粋なJSON文字列として出力してください。
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


