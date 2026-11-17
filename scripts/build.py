#!/usr/bin/env python3
"""content/ と data/calendar.json から feed.json を組み立て、形式をチェックする。

content/pages/<name>.json  と  content/pages/<name>.html  （固定ページ）
content/posts/<name>.json  と  content/posts/<name>.html  （記事）
.json にはメタ情報（id, title, slug, ...）、.html には本文を書く。
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_POSTS = 40
ID_RE = re.compile(r"^[a-z0-9-]+$")
CATEGORIES = {"新型車", "比較", "カー用品", "旧車"}
errors = []


def load_items(kind):
    items = []
    for meta_path in sorted((ROOT / "content" / kind).glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        html_path = meta_path.with_suffix(".html")
        if not html_path.exists():
            errors.append(f"{meta_path.name}: 本文 {html_path.name} がありません")
            continue
        meta["content"] = html_path.read_text(encoding="utf-8").strip()
        meta["type"] = "page" if kind == "pages" else "post"
        items.append(meta)
    return items


def calendar_html():
    cal = json.loads((ROOT / "data" / "calendar.json").read_text(encoding="utf-8"))
    entries = sorted(cal.get("entries", []), key=lambda e: e.get("release_date") or "9999")
    out = [
        "<p>国内で発表・発売される新型車、フルモデルチェンジ、一部改良を発売日順にまとめています。"
        "掲載するのはメーカーの公式発表で確認できたものだけです。</p>",
        f"<p>最終更新：{html.escape(cal.get('updated', ''))}</p>",
    ]
    if not entries:
        out.append("<p>現在、掲載できる情報を集めています。</p>")
    else:
        out.append('<table><thead><tr><th>発売日</th><th>メーカー</th><th>車種</th>'
                   '<th>内容</th><th>価格（税込）</th><th>出典</th></tr></thead><tbody>')
        for e in entries:
            src = e.get("source_url", "")
            link = f'<a href="{html.escape(src)}" target="_blank" rel="noopener">公式</a>' if src else ""
            out.append(
                "<tr>" + "".join(f"<td>{html.escape(str(e.get(k, '') or '未発表'))}</td>"
                                 for k in ("release_date", "maker", "model", "change", "price"))
                + f"<td>{link}</td></tr>"
            )
        out.append("</tbody></table>")
    return "\n".join(out)


def main():
    pages = load_items("pages")
    for p in pages:
        if p.get("id") == "page-calendar":
            p["content"] = calendar_html()

    posts = load_items("posts")
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    posts = posts[:MAX_POSTS]

    seen = set()
    for it in pages + posts:
        name = it.get("id", "(idなし)")
        for key in ("id", "title", "content"):
            if not it.get(key):
                errors.append(f"{name}: {key} が空です")
        if name in seen:
            errors.append(f"{name}: id が重複しています")
        seen.add(name)
        if not ID_RE.match(name):
            errors.append(f"{name}: id は英小文字・数字・ハイフンのみ")
        if it["type"] == "post" and it.get("category") not in CATEGORIES:
            errors.append(f"{name}: category は {sorted(CATEGORIES)} のどれか")
        if "<script" in it.get("content", "").lower():
            errors.append(f"{name}: <script> は使えません")

    if errors:
        print("エラー:\n  " + "\n  ".join(errors))
        sys.exit(1)

    feed = {"items": pages + posts}
    (ROOT / "feed.json").write_text(json.dumps(feed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: 固定ページ {len(pages)} 件 / 記事 {len(posts)} 件 → feed.json")


if __name__ == "__main__":
    main()
