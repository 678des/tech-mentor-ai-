import os
from pathlib import Path
from dotenv import load_dotenv  

print("スクリプト読み込み")
load_dotenv()

import feedparser
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import json
from pydantic import BaseModel
from typing import Any, List, Dict

# CRUDモジュールのインポート
from crud import get_all_urls, save_articles


    # 6. Geminiモデルの呼び出し（JSON出力を強制する設定を入れる）
GEMINI_API_KEY=os.environ["GEMINI_API_KEY"]
#genai.configure(api_key=os.environ["GEMINI_API_KEY"]) 
genai.configure(api_key=GEMINI_API_KEY) 
    

# 1. 構造の定義（TypeScriptの型定義と一対一になる）
class SelectedArticle(BaseModel):
    title: str
    url: str
    reason: str  # なぜ今読むべきなのか（選定理由）

class NewsResponse(BaseModel):
    mentor_message: str            # 最後のメンターメッセージ
    selected_articles: List[SelectedArticle]  # AIが選んだ3〜5件
    all_candidates_count: int      # 取得した全記事数などのメタ情報

    
app = FastAPI()

# React(Vite)からのリクエストを許可するCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Viteのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# 2. ユーザーのコンテキスト
user_context = {
    "subjects": [
        "情報数学", "データ構造とアルゴリズム", "情報デザイン基礎", 
        "Linux演習基礎", "英語", "情報関連法規と情報倫理",
        "C++","Java","Python"
    ],
    "interests": [
        "Next.js", "TypeScript", "AIエージェント開発", "AI駆動開発", 
        "C# / Unity / Blender", "30卒", "AI代替による雇用の減少", "話題の技術"
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


@app.get("/api/news")
def get_news():
    
    checked_urls = get_all_urls()
    # 3. RSSフィードのURLリスト
    rss_urls = [
    "https://zenn.dev/feed",                  # Zenn（技術トレンド）
    "https://qiita.com/popular-items/feed",     # Qiita（人気記事）
    ]
    candidates: List[dict[str, str]] = []
    for url in rss_urls:
        feed: Any = feedparser.parse(url)
        for entry in feed.entries[:25]:
            title = entry.title
            link = entry.link
            # 概要を取得（HTMLタグ除去や長さ調整）
            summary = getattr(entry, 'summary', '概要なし')

            if link in checked_urls:continue
            print("タイトル",title,link,end="\n")
            candidates.append({
                "title": title,
                "url": link,
                "summary": summary[:200]  # 冒頭200文字程度
            })

    # タイトルの重複排除
    unique_candidates: List[dict[str, str]] = []
    seen_titles: set[str] = set()
    for c in candidates:
        if c["title"] not in seen_titles:
            seen_titles.add(c["title"])
            unique_candidates.append(c)

    print(f"✅ {len(unique_candidates)} 件の個別記事を取得しました\n")
    save_articles(unique_candidates)
    return unique_candidates

    candidate_text_list = []
    for idx, item in enumerate(unique_candidates, 1):
        candidate_text_list.append(
            f"[{idx}] タイトル: {item['title']}\n"
            f"URL: {item['link']}\n"
            f"概要: {item['summary']}\n")

    formatted_candidates = "\n".join(candidate_text_list)

# 5. プロンプトの構築
    prompt = f"""
あなたはユーザーの専属キャリアメンター兼・優秀な技術選定パーソナライズAIエージェントです。

【ユーザーのコンテキスト】
- 履修科目: {', '.join(user_context['subjects'])}
- 関心・テーマ: {', '.join(user_context['interests'])}
- 現在の心理的状況・悩み: {user_context['situation'][0]}

【候補記事リスト】
{formatted_candidates}

【指示】
候補リストから、ユーザーの悩みやモチベーション向上に効く記事を3〜5件選定し、必ず以下のJSON構造のみで出力してください（Markdownのバッククォート等も不要）。

{{
  "mentor_message": "AI時代にポートフォリオを作る意味や強みに関する短く温かいメッセージ",
  "selected_articles": [
    {{
      "title": "記事タイトル",
      "url": "記事URL",
      "reason": "選定理由（悩みにどう寄り添い、どんな気づきを与えるか）"
    }}
  ]
}}
"""


    # response_mime_type を指定すると綺麗にJSONだけを返してくれる
    model = genai.GenerativeModel(
        'gemini-3.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )


    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(f"Error generating content: {e}")
        return {
            "mentor_message": "",
            "selected_articles": [],
            "all_candidates_count": len(unique_candidates)
        }

    # 7. JSON文字列をPythonの辞書（dict）に変換して返却
    result = json.loads(response.text)
    
    return {
        "mentor_message": result.get("mentor_message", ""),
        "selected_articles": result.get("selected_articles", []),
        "all_candidates_count": len(unique_candidates)
    }






from crud import get_all_urls, save_articles, get_all_articles

@app.get("/api/articles")
def get_articles_endpoint():
    """
    Supabaseに保存されているすべての記事をJSON形式でフロントエンドに返す
    """
    articles = get_all_articles()
    return {
        "count": len(articles),
        "articles": articles
    }