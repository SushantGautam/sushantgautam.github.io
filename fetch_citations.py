from scholarly import scholarly, ProxyGenerator
import json
import os

# Set up the proxy generator
pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

# Fetch author's publications
author = scholarly.search_author_id("t3Iie8cAAAAJ")
author = scholarly.fill(author, sections=["publications"])
publications = author.get("publications", [])

# Strip down to relevant fields and convert to JSON-safe
pubs_data = []
for pub in publications:
    bib = pub.get("bib", {})
    pubs_data.append({
        "bib": {
            "title": bib.get("title", ""),
            "author": bib.get("author", ""),
            "pub_year": int(bib.get("pub_year", 0)) if bib.get("pub_year") else 0,
            "citation": bib.get("citation", ""),
        },
        "num_citations": pub.get("num_citations", 0),
        "pub_url": pub.get("pub_url", ""),
        "cites_id": pub.get("cites_id", []),
    })

json_data = json.dumps(pubs_data)

# Read the HTML template
html_template = """
<div class="container">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        body, .container { padding: 0; width: 100%; font-size: 14px; line-height: 1.4; overflow-x: hidden; }
        .list-group-item, .form-check-label, a { font-size: inherit; }
        .list-group-item { padding: 5px 10px; border: none; }
        .form-check-input { transform: scale(0.8); }
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
    document.addEventListener("DOMContentLoaded", () => {
        const publications = REPLACEME;
        const list = document.getElementById("publication-list");
        const toTitle = str => str.replace(/\\w\\S*/g, t => t[0].toUpperCase() + t.slice(1).toLowerCase());

        const render = sortBy => {
            publications.sort((a, b) => sortBy === "year"
                ? b.bib.pub_year - a.bib.pub_year
                : b.num_citations - a.num_citations);

            list.innerHTML = publications.map(p => {
                const url = p.pub_url || (p.cites_id?.length
                    ? `https://scholar.google.com/scholar?cluster=${p.cites_id[0]}`
                    : `https://www.google.com/search?q=${encodeURIComponent(p.bib.title)}`);
                return `
            <li class="list-group-item">
              <a href="${url}" target="_blank"><strong>${toTitle(p.bib.title)}</strong></a>
              ${p.num_citations > 2 ? `<small> - Cited by: ${p.num_citations}</small>` : ""}
              ${p.bib.author ? `<br><em>${p.bib.author}</em>` : ""}
              <br><em><a target="_blank" href="https://www.google.com/search?q=${p.bib.citation}"${p.bib.citation}</a></em>
            </li>`;
            }).join("");
        };

        document.querySelectorAll("input[name='sort']").forEach(radio =>
            radio.addEventListener("change", () => render(radio.value))
        );

        render("citations");
    });
</script>
"""

# Inject data and save to HTML
html_output = html_template.replace("REPLACEME", json_data)
with open("citations.html", "w", encoding="utf-8") as f:
    f.write(html_output)
