import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from xml.sax.saxutils import escape

USER = "PedroBett-dev"
PROMPT = "pedro@bett"
BIRTHDAY = date(2007, 11, 20)


INFO = [
    ("#", PROMPT),
    ("OS", "macOS, Windows, Linux"),
    ("Uptime", "{uptime}"),
    ("Local", "Brasil"),
    ("IDE", "VS Code, GoLand"),
    None,
    ("Linguagens.Programação", "Go, C, Python, Harbour"),
    ("Linguagens.Idiomas", "Português, Inglês(Básico)"),
    None,
    ("Estudando", "Algoritmos, Arquitetura de Computadores"),
    ("Construindo", "APIs em Go"),
    None,
    ("#", "Contato"),
    ("LinkedIn", "pedro-henrique-camilo-bett"),
    ("GitHub", USER),
    None,
    ("#", "GitHub Stats"),
    ("Repos", "{repos}"),
    ("Contribuições", "{contributed}"),
    ("Stars", "{stars}"),
    ("Commits", "{commits}"),
    ("Seguidores", "{followers}"),
]

WIDTH, HEIGHT = 985, 530
ROW_CHARS = 57
ASCII_ROWS = 25
INFO_X = 400
LINE_H = 20

THEMES = {
    "dark": dict(bg="#161b22", fg="#c9d1d9", key="#ffa657", value="#a5d6ff", dots="#616e7f"),
    "light": dict(bg="#f6f8fa", fg="#24292f", key="#953800", value="#0a3069", dots="#c2cfde"),
}

ART = [
    '  .--------------------------------.',
    '  | .----------------------------. |',
    '  | | $ go run main.go           | |',
    '  | | func main() {              | |',
    '  | |     fmt.Println("Olá!")    | |',
    '  | | }                          | |',
    '  | |                            | |',
    '  | | Olá!                       | |',
    '  | | $ _                        | |',
    "  | '----------------------------' |",
    "  '--------------------------------'",
    ' /  ::::::::::::::::::::::::::::::  \\',
    '/  ::::::::::::::::::::::::::::::::  \\',
    "'------------------------------------'",
]


def graphql(query, variables):
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch_stats():
    user = graphql(
        """query($login: String!) {
          user(login: $login) {
            createdAt
            followers { totalCount }
            repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
            repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
              totalCount
              nodes { stargazerCount }
            }
          }
        }""",
        {"login": USER},
    )["user"]

    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    commits = 0
    for year in range(created.year, now.year + 1):
        start = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        end = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        data = graphql(
            """query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                  totalCommitContributions
                  restrictedContributionsCount
                }
              }
            }""",
            {"login": USER, "from": start.isoformat(), "to": end.isoformat()},
        )["user"]["contributionsCollection"]
        commits += data["totalCommitContributions"] + data["restrictedContributionsCount"]

    return {
        "uptime": uptime(BIRTHDAY, now.date()),
        "repos": f"{user['repositories']['totalCount']:,}",
        "contributed": f"{user['repositoriesContributedTo']['totalCount']:,}",
        "stars": f"{sum(r['stargazerCount'] for r in user['repositories']['nodes']):,}",
        "commits": f"{commits:,}",
        "followers": f"{user['followers']['totalCount']:,}",
    }


def uptime(start: date, today: date):
    years = today.year - start.year
    months = today.month - start.month
    days = today.day - start.day
    if days < 0:
        months -= 1
        days += (today.replace(day=1) - timedelta(days=1)).day
    if months < 0:
        years -= 1
        months += 12

    def plural(n, one, many):
        return f"{n} {one if n == 1 else many}"

    return ", ".join([plural(years, "ano", "anos"), plural(months, "mês", "meses"), plural(days, "dia", "dias")])


def ascii_art():
    top = (ASCII_ROWS - len(ART)) // 2
    return [""] * top + ART


def info_lines(stats):
    out = []
    for item in INFO:
        if item is None:
            out.append('<tspan class="dots">. </tspan>')
            continue
        key, value = item
        if key == "#":
            title = value if value == PROMPT else f"- {value}"
            rule = "—" * max(ROW_CHARS - len(title) - 1, 0)
            out.append(f"{escape(title)} <tspan class=\"dots\">{rule}</tspan>")
            continue
        value = value.format(**stats)
        parts = key.split(".")
        key_svg = '<tspan class="dots">.</tspan>'.join(
            f'<tspan class="key">{escape(p)}</tspan>' for p in parts
        )
        used = 2 + len(key) + 1 + len(value) + 2
        dots = "." * max(ROW_CHARS - used, 1)
        out.append(
            f'<tspan class="dots">. </tspan>{key_svg}:'
            f'<tspan class="dots"> {dots} </tspan><tspan class="value">{escape(value)}</tspan>'
        )
    return out


def render(theme, portrait, stats):
    t = THEMES[theme]
    ascii_svg = "\n".join(
        f'<tspan x="15" y="{30 + i * LINE_H}">{escape(line)}</tspan>' for i, line in enumerate(portrait)
    )
    info_svg = "\n".join(
        f'<tspan x="{INFO_X}" y="{30 + i * LINE_H}">{line}</tspan>' for i, line in enumerate(info_lines(stats))
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}px" height="{HEIGHT}px" font-family="Consolas, Menlo, 'DejaVu Sans Mono', monospace" font-size="16px">
<style>
text, tspan {{ white-space: pre; }}
.key {{ fill: {t['key']}; }}
.value {{ fill: {t['value']}; }}
.dots {{ fill: {t['dots']}; }}
</style>
<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t['bg']}" rx="15"/>
<text fill="{t['fg']}">
{ascii_svg}
</text>
<text fill="{t['fg']}">
{info_svg}
</text>
</svg>
"""


def main():
    stats = fetch_stats()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portrait = ascii_art()
    for theme in THEMES:
        svg = render(theme, portrait, stats)
        with open(os.path.join(root, f"{theme}_mode.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
    print("SVGs gerados:", stats)


if __name__ == "__main__":
    main()
