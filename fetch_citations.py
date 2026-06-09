import json
import os
import time

import serpapi

AUTHOR_ID = "t3Iie8cAAAAJ"
PAGE_SIZE = 100
SERPAPI_API_KEY_ENV = "SERPAPI_API_KEY"


def fetch_author_publications(author_id: str, api_key: str):
    all_articles = []
    start = 0

    while True:
        results = serpapi.search({
            "engine": "google_scholar_author",
            "author_id": author_id,
            "hl": "en",
            "num": PAGE_SIZE,
            "start": start,
            "api_key": api_key,
        })

        results = dict(results)

        if "error" in results:
            raise RuntimeError(results["error"])

        articles = results.get("articles", [])
        if not articles:
            break

        all_articles.extend(articles)
        print(f"Fetched {len(articles)}; total = {len(all_articles)}")

        if len(articles) < PAGE_SIZE:
            break

        start += PAGE_SIZE
        time.sleep(1)

    return all_articles


def normalize_article(article: dict) -> dict:
    cited_by = article.get("cited_by") or {}
    citation_id = article.get("citation_id")
    cited_by_link = cited_by.get("link")
    cites_id = []

    if cited_by_link and "cites=" in cited_by_link:
        cites_part = cited_by_link.split("cites=", 1)[1].split("&", 1)[0]
        cites_id = [item for item in cites_part.split(",") if item]

    return {
        "container_type": "Publication",
        "source": "SERPAPI_GOOGLE_SCHOLAR_AUTHOR",
        "bib": {
            "title": article.get("title") or "",
            "pub_year": str(article.get("year") or ""),
            "author": article.get("authors") or "",
            "citation": article.get("publication") or "",
        },
        "filled": False,
        "author_pub_id": citation_id,
        "num_citations": int(cited_by.get("value") or 0),
        "pub_url": article.get("link"),
        "citedby_url": cited_by_link,
        "cites_id": cites_id,
    }


def build_html(publications: list[dict]) -> str:
    json_data = json.dumps(publications, ensure_ascii=False)

    html_template = """
<div class="container">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body,
        .container {
            padding: 0;
            width: 100%;
            font-size: 14px;
            line-height: 1.4;
            overflow-x: hidden;
        }

        .list-group-item,
        .form-check-label,
        a {
            font-size: inherit;
        }

        .list-group-item {
            padding: 6px 10px;
            border: none;
        }

        .form-check-input {
            transform: scale(0.8);
        }

        .citation-meta {
            color: #555;
        }

        .citation-links small {
            margin-right: 8px;
        }
    </style>
    <label>Sort by:</label>
    <div class="form-check form-check-inline">
        <input class="form-check-input" type="radio" name="sort" value="year" id="year">
        <label class="form-check-label" for="year">Year</label>
    </div>
    <div class="form-check form-check-inline">
        <input class="form-check-input" type="radio" name="sort" value="citations" id="citations" checked>
        <label class="form-check-label" for="citations">Relevance</label>
    </div>
    <ul id="publication-list" class="list-group mt-2"></ul>
</div>

<script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.min.js"></script>
<script>
    function initCitationsWidget() {
        const publications = REPLACEME;
        const list = document.getElementById("publication-list");

        const escapeHtml = value => String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

        const safeUrl = value => {
            const url = String(value || "");
            return /^https?:\/\//i.test(url) ? url : "";
        };

        const highlightAuthor = authors => escapeHtml(authors)
            .replace(/Sushant Gautam/g, "<b>Sushant Gautam</b>")
            .replace(/S Gautam/g, "<b>S Gautam</b>");

        const render = sortBy => {
            publications.sort((a, b) => sortBy === "year"
                ? Number(b.bib.pub_year || 0) - Number(a.bib.pub_year || 0)
                : Number(b.num_citations || 0) - Number(a.num_citations || 0));

            list.innerHTML = publications.map(p => {
                const title = escapeHtml(p.bib.title);
                const year = escapeHtml(p.bib.pub_year);
                const authors = highlightAuthor(p.bib.author);
                const citation = escapeHtml(p.bib.citation);
                const pubUrl = safeUrl(p.pub_url) || (p.cites_id?.length
                    ? `https://scholar.google.com/scholar?cluster=${encodeURIComponent(p.cites_id[0])}`
                    : `https://www.google.com/search?q=${encodeURIComponent(p.bib.title)}`);
                const citedByUrl = safeUrl(p.citedby_url);
                const citations = Number(p.num_citations || 0);
                const venueUrl = p.bib.citation
                    ? `https://www.google.com/search?q=${encodeURIComponent(p.bib.citation)}`
                    : "";

                return `
            <li class="list-group-item">
              <a href="${pubUrl}" target="_blank" rel="noopener noreferrer"><strong>${title}</strong></a>
              ${year ? `<small class="citation-meta">(${year})</small>` : ""}<br>
              ${authors ? `<em>${authors}</em><br>` : ""}
              ${citation ? `<span class="citation-meta">In <em><a target="_blank" rel="noopener noreferrer" href="${venueUrl}">${citation}</a></em></span><br>` : ""}
              <span class="citation-links">
                ${citations > 0 ? `<small>${citedByUrl ? `<a target="_blank" rel="noopener noreferrer" href="${citedByUrl}">Cited by ${citations}</a>` : `Cited by ${citations}`}</small>` : ""}
                ${pubUrl ? `<small><a target="_blank" rel="noopener noreferrer" href="${pubUrl}">Scholar record</a></small>` : ""}
              </span>
            </li>`;
            }).join("");
        };

        document.querySelectorAll("input[name='sort']").forEach(radio =>
            radio.addEventListener("change", () => render(radio.value))
        );

        render("citations");
    };

    initCitationsWidget();
</script>
"""

    return html_template.replace("REPLACEME", json_data)


def main() -> None:
    api_key = os.environ.get(SERPAPI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {SERPAPI_API_KEY_ENV}")

    articles = fetch_author_publications(AUTHOR_ID, api_key)
    publications = [normalize_article(article) for article in articles]
    publications_sorted = sorted(publications, key=lambda x: x.get("bib", {}).get("title", "").lower())

    with open("citations.json", "w", encoding="utf-8") as f:
        json.dump(publications_sorted, f, indent=4, ensure_ascii=False)

    with open("citations.html", "w", encoding="utf-8") as f:
        f.write(build_html(publications))


if __name__ == "__main__":
    main()
