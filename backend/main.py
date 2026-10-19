import os
from dotenv import load_dotenv  

load_dotenv()

import feedparser
import google.generativeai as genai


# 1. APIキーの設定

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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

# 3. RSSフィードのURLリスト
rss_urls = [
    "https://zenn.dev/feed",                  # Zenn（技術トレンド）
    "https://qiita.com/popular-items/feed",     # Qiita（人気記事）
]

checked_urls = set([
    "https://zenn.dev/hand_dot/articles/ecb391d4322330",
    "https://zenn.dev/hand_dot/articles/ecb391d4322330",
    "https://qiita.com/satoshot/items/3308a7e025cd9f049813?utm_campaign=popular_items&utm_medium=feed&utm_source=popular_items",
    "https://zenn.dev/ara_jlu/articles/per-task-review-dropped"
])

print("📡 RSSフィードから記事データを収集中...")

# 4. RSSから記事情報（タイトル・URL・概要）を取得
candidates = []
for url in rss_urls:
    feed = feedparser.parse(url)
    for entry in feed.entries[:25]:
        title = entry.title
        link = entry.link
        # 概要を取得（HTMLタグ除去や長さ調整）
        summary = getattr(entry, 'summary', '概要なし')
       
        if link in checked_urls:continue
        print("タイトル",title,link,end="\n")
        candidates.append({
            "title": title,
            "link": link,
            "summary": summary[:200]  # 冒頭200文字程度
        })

# タイトルの重複排除
unique_candidates = []
seen_titles = set()
for c in candidates:
    if c["title"] not in seen_titles:
        seen_titles.add(c["title"])
        unique_candidates.append(c)

print(f"✅ {len(unique_candidates)} 件の個別記事を取得しました。AIエージェントが分析中...\n")

# 候補テキストの整形（chr(10)で改行連結）
candidate_text_list = []
for idx, item in enumerate(unique_candidates, 1):
    candidate_text_list.append(
        f"[{idx}] タイトル: {item['title']}\n"
        f"    URL: {item['link']}\n"
        f"    概要: {item['summary']}\n"
    )

formatted_candidates = "\n".join(candidate_text_list)

# 5. プロンプトの構築
prompt = f"""
あなたはユーザーの専属キャリアメンター兼・優秀な技術選定パーソナライズAIエージェントです。

【ユーザーのコンテキスト】
- 履修科目: {', '.join(user_context['subjects'])}
- 関心・テーマ: {', '.join(user_context['interests'])}
- 現在の心理的状況・悩み:
{user_context['situation'][0]}

【候補記事リスト】
{formatted_candidates}

【指示】
1. 候補リストの中から、ユーザーの興味・履修科目だけでなく、**「今の悩みやモチベーションの停滞を打破する助けになるような記事（AI時代のエンジニアの価値、開発プロセスの楽しみ、デザイン/基礎理論との掛け合わせなど）」**を含めて 3〜5 件選定してください。
2. 各選定記事について以下の形式で出力してください：
   - 記事タイトルとURL
   - なぜ今、このユーザーが読むべきなのか（悩みにどう寄り添い、どんな気づきを与えるか）
3. 最後に、AI時代にポートフォリオを作る意味や、ユーザーの持つ強み（情報デザインや基礎理論、3D表現などとの掛け合わせ）についての短く温かいメンターメッセージを添えてください。
"""

# 6. Geminiモデルの呼び出し
model = genai.GenerativeModel('gemini-3.6-flash')
response = model.generate_content(prompt)

print("=== 🎯 AIエージェントの判定＆メンターフィードバック ===")
print(response.text)