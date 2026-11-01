import os
import json
from typing import List, Dict, Any
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
EMBEDDING_DIMENSIONS = 1536
GENERATION_MODEL = os.environ.get("GEMINI_GENERATION_MODEL", "gemini-2.5-flash")


def build_article_embedding_text(article: Dict[str, Any]) -> str:
    """Build the text representation used for article retrieval."""
    parts = [
        f"タイトル: {(article.get('title') or '').strip()}",
        f"RSS概要: {(article.get('summary') or '').strip()}",
    ]
    return "\n".join(part for part in parts if part.split(": ", 1)[1])


def create_embedding(text: str) -> List[float]:
    """Create a 1536-dimensional embedding compatible with articles.embedding."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Geminiから埋め込みベクトルが返されませんでした")
    values = response.embeddings[0].values
    if len(values) != EMBEDDING_DIMENSIONS:
        raise ValueError(f"埋め込み次元数が不正です: {len(values)}")
    return values


def generate_rag_answer(query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    RAG回答生成: ベクトル検索で取得した関連記事を根拠に、
    質問に対する分析・回答およびキーインサイトを生成する。
    """
    if not articles:
        return {
            "answer": "関連する記事が見つかりませんでした。別のキーワードや表現で再度お試しください。",
            "key_insights": [],
            "referenced_articles": [],
        }

    # 記事コンテキストの整形
    articles_context = []
    for a in articles:
        articles_context.append({
            "id": a.get("id"),
            "title": a.get("title"),
            "url": a.get("url"),
            "summary": (a.get("summary") or "")[:1000],
        })

    system_instruction = """
あなたは、日本のIT業界の新卒採用・エンジニア育成・AI活用に関する課題や本音を分析するリサーチアナリストです。
提供された参考記事群（Zenn、Qiita、noteなどから収集されたリアルな声）のみを根拠として、ユーザーの質問や疑問に対する回答を作成してください。

【回答方針】
1. 一般論や建前ではなく、記事群から読み取れる「生々しい本音」「リアルな悩み・課題」「現場の葛藤や失敗談」にフォーカスしてください。
2. 回答本文（answer）はマークダウン形式で、読みやすく構造化（見出し、箇条書き等）して記述してください。
3. 根拠となった記事がある場合は、文中で [記事タイトル](URL) の形式で自然に言及・リンクしてください。
4. 提供された記事に書かれていない事実を勝手に捏造しないでください。

【出力形式】
必ず次のJSON構造のみで返してください:
{
  "answer": "マークダウン形式の回答本文",
  "key_insights": ["記事群から抽出された重要ポイント・洞察（箇条書き2〜4個）"]
}
"""

    prompt = f"""
【ユーザーの質問】
{query}

【参考記事群】
{json.dumps(articles_context, ensure_ascii=False, indent=2)}
"""

    try:
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        data = json.loads(response.text)
        return {
            "answer": data.get("answer", ""),
            "key_insights": data.get("key_insights", []),
            "referenced_articles": articles,
        }
    except Exception as e:
        print(f"RAG回答生成中にエラーが発生しました: {e}")
        return {
            "answer": f"回答の生成中にエラーが発生しました: {e}",
            "key_insights": [],
            "referenced_articles": articles,
        }
