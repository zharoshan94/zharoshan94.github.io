#!/usr/bin/env python3

import re
import html
import matplotlib.pyplot as plt

from pathlib import Path
from pybtex.database import parse_file
from wordcloud import WordCloud, STOPWORDS


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

BIB_FILE = SCRIPT_DIR / "pubs.bib"
OUTPUT_DIR = ROOT_DIR / "images"
OUTPUT_IMAGE = OUTPUT_DIR / "abstract_wordcloud.png"

CUSTOM_STOPWORDS = {
    "study", "studies", "paper", "papers", "analysis", "result", "results",
    "using", "used", "show", "shows", "based", "across",
    "future", "present", "observed", "observation", "model", "models", "data",
    "approach", "effect", "effects", "response", "responses", "variability",
    "increase", "increases", "decrease", "decreases",

    "heat", "event", "events", "countries", "country", "due", "levels", "early", "pre","post", 
    "region", "regions",  "episode", "episodes","findings", "find", "finds", "finding",
    "plain", "monsoon", "indian", "pakistan", "average","presented", 'compared', "related", "transfer",
    "year", "march", "april", "daily", "record", "recent", "first","including", "made", "plains"
    "large", "strong", "maximum", "level", "times", "role", "resulting", "analyse"
}


def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    text = re.sub(r"[^A-Za-z\\s-]", " ", text)
    text = re.sub(r"\b[a-zA-Z]\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\bclimate change\b", "climate_change", text, flags=re.I)
    return text.strip().lower()


def get_field(entry, *names):
    for name in names:
        value = entry.fields.get(name)
        if value:
            return value
    return None


def main():
    if not BIB_FILE.exists():
        raise FileNotFoundError(f"BibTeX file not found: {BIB_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bib_data = parse_file(str(BIB_FILE))
    abstracts = []
    used_titles = []
    missing_titles = []

    for key, entry in bib_data.entries.items():
        title = get_field(entry, "title") or key
        abstract = get_field(entry, "abstract")

        if abstract:
            abstracts.append(abstract)
            used_titles.append(title)
        else:
            missing_titles.append(title)

    if not abstracts:
        raise RuntimeError(
            "No abstracts found in pubs.bib. "
            "Add abstract = {...} fields to the BibTeX entries you want to use."
        )

    combined_text = clean_text(" ".join(abstracts))

    stopwords = set(STOPWORDS)
    stopwords.update(CUSTOM_STOPWORDS)

    wordcloud = WordCloud(
        width=1400,
        height=900,
        background_color="white",
        stopwords=stopwords,
        collocations=False,
        max_words=120,
        colormap="viridis",
        prefer_horizontal=0.9
    ).generate(combined_text)

    plt.figure(figsize=(14, 9))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(str(OUTPUT_IMAGE), dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"Saved word cloud: {OUTPUT_IMAGE}")
    print(f"Papers with abstracts used: {len(used_titles)}")

    if used_titles:
        print("\nUsed papers:")
        for title in used_titles:
            print(f"- {title}")

    if missing_titles:
        print("\nPapers with no abstract field in pubs.bib:")
        for title in missing_titles:
            print(f"- {title}")


if __name__ == "__main__":
    main()