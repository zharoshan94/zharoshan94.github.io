#!/usr/bin/env python
# coding: utf-8


from pybtex.database.input import bibtex
import pybtex.database.input.bibtex
from time import strptime
import html
import os
import re



publist = {
    "journal": {
        "file": "pubs.bib",
        "venuekey": "journal",
        "venue-pretext": "",
        "collection": {
            "name": "publications",
            "permalink": "/publication/"
        },
        "category": "manuscripts"
    }
}



html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}



def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)



def clean_text(text):
    if not text:
        return ""
    text = str(text).replace("{", "").replace("}", "").replace("\\", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text



def clean_slug(text):
    clean_title = clean_text(text).replace(" ", "-")
    url_slug = re.sub(r"\[.*?\]|[^a-zA-Z0-9_-]", "", clean_title)
    url_slug = re.sub(r"-{2,}", "-", url_slug).strip("-")
    return url_slug



def parse_month(month_value):
    if not month_value:
        return "01"
    month_value = str(month_value).strip()


    if month_value.isdigit():
        m = int(month_value)
        return f"{m:02d}" if 1 <= m <= 12 else "01"


    try:
        return f"{strptime(month_value[:3], '%b').tm_mon:02d}"
    except ValueError:
        return "01"



def parse_day(day_value):
    if not day_value:
        return "01"
    day_value = str(day_value).strip()
    if day_value.isdigit():
        d = int(day_value)
        return f"{d:02d}" if 1 <= d <= 31 else "01"
    return "01"



def initials_from_names(names):
    initials = []
    for n in names or []:
        n = str(n).strip()
        if n:
            initials.append(n[0] + ".")
    return initials



def format_person_last_initials(person):
    """
    Roshan Jha -> Jha, R.
    M. P. Byrne -> Byrne, M. P.
    """
    last = " ".join(person.last_names) if person.last_names else ""
    first_parts = list(person.first_names or []) + list(person.middle_names or [])
    initials = initials_from_names(first_parts)


    if initials:
        return f"{last}, {' '.join(initials)}"
    return last



def is_jha(person):
    last_names = [str(x).lower().strip() for x in (person.last_names or [])]
    first_names = [str(x).lower().strip().replace(".", "") for x in (person.first_names or [])]
    middle_names = [str(x).lower().strip().replace(".", "") for x in (person.middle_names or [])]


    if "jha" not in last_names:
        return False


    all_given = first_names + middle_names
    if not all_given:
        return True


    for fn in all_given:
        if fn == "roshan" or fn == "r":
            return True


    return True



def person_key(person):
    """
    Key for duplicate removal while preserving order.
    """
    last = " ".join(person.last_names or []).lower().strip()
    first = " ".join(person.first_names or []).lower().replace(".", "").strip()
    middle = " ".join(person.middle_names or []).lower().replace(".", "").strip()
    return (last, first, middle)



def dedupe_persons(persons):
    """
    Remove duplicate authors while preserving order.
    """
    seen = set()
    unique = []
    for p in persons:
        key = person_key(p)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique



def join_names(names):
    if len(names) == 0:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f" and {names[-1]}"



def format_author_list_md(persons, max_names=10):
    """
    Always:
    - deduplicate authors
    - bold Jha, R.
    - show max 10 names
    - if Jha is not in shown names but exists later, append
      '(authors including **Jha, R.**)'
    """
    persons = dedupe_persons(persons)


    formatted_all = []
    jha_index = None


    for idx, p in enumerate(persons):
        if is_jha(p):
            name = "**Jha, R.**"
            if jha_index is None:
                jha_index = idx
        else:
            name = format_person_last_initials(p)
        formatted_all.append(name)


    shown = formatted_all[:max_names]
    author_str = join_names(shown)


    if len(formatted_all) > max_names:
        if jha_index is not None and jha_index >= max_names:
            author_str += " (authors including **Jha, R.**)"
        else:
            author_str += " et al."


    return author_str



def format_author_list_plain(persons, max_names=10):
    """
    Plain text version matching markdown logic.
    """
    persons = dedupe_persons(persons)


    formatted_all = []
    jha_index = None


    for idx, p in enumerate(persons):
        if is_jha(p):
            name = "Jha, R."
            if jha_index is None:
                jha_index = idx
        else:
            name = format_person_last_initials(p)
        formatted_all.append(name)


    shown = formatted_all[:max_names]
    author_str = join_names(shown)


    if len(formatted_all) > max_names:
        if jha_index is not None and jha_index >= max_names:
            author_str += " (authors including Jha, R.)"
        else:
            author_str += " et al."


    return author_str



def extract_clean_doi(fields):
    doi = clean_text(fields.get("doi", ""))
    if ";" in doi:
        doi = doi.split(";")[0].strip()
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    return doi.strip()



def extract_best_url(fields):
    doi = extract_clean_doi(fields)
    raw_url = fields.get("url", "")


    if doi:
        return f"https://doi.org/{doi}"


    if raw_url:
        urls = re.findall(r"https?://[^\s\]]+", raw_url)
        if urls:
            return urls[-1].strip()


        raw_url = raw_url.strip()
        if raw_url.startswith("http://") or raw_url.startswith("https://"):
            return raw_url


    return ""



for pubsource in publist:
    parser = bibtex.Parser()
    bibdata = parser.parse_file(publist[pubsource]["file"])


    for bib_id in bibdata.entries:
        pub_year = "1900"
        pub_month = "01"
        pub_day = "01"


        b = bibdata.entries[bib_id].fields


        try:
            pub_year = str(b["year"]).strip()
            pub_month = parse_month(b.get("month", "01"))
            pub_day = parse_day(b.get("day", "01"))
            pub_date = f"{pub_year}-{pub_month}-{pub_day}"


            title_clean = clean_text(b["title"])
            url_slug = clean_slug(b["title"])


            md_filename = f"{pub_date}-{url_slug}.md".replace("--", "-")
            html_filename = f"{pub_date}-{url_slug}".replace("--", "-")


            persons = bibdata.entries[bib_id].persons["author"]
            authors_plain = format_author_list_plain(persons, max_names=10)
            authors_md = format_author_list_md(persons, max_names=10)


            venue = clean_text(
                publist[pubsource]["venue-pretext"] + b[publist[pubsource]["venuekey"]]
            )


            volume = clean_text(b.get("volume", ""))
            pages = clean_text(b.get("pages", ""))
            doi = extract_clean_doi(b)
            paperurl = extract_best_url(b)


            citation_plain = f'{authors_plain}: "{title_clean}," {venue}'
            if volume:
                citation_plain += f", {volume}"
            if pages:
                citation_plain += f", {pages}"
            citation_plain += "."


            title_md = f"[{title_clean}]({paperurl})" if paperurl else title_clean
            citation_md = f"{authors_md}: {title_md}, *{venue}*"
            if volume:
                citation_md += f", {volume}"
            if pages:
                citation_md += f", {pages}"
            citation_md += "."


            md = "---\n"
            md += f'title: "{html_escape(title_clean)}"\n'
            md += f'collection: {publist[pubsource]["collection"]["name"]}\n'
            md += f'permalink: {publist[pubsource]["collection"]["permalink"]}{html_filename}\n'
            md += f"date: {pub_date}\n"
            md += f'venue: "{html_escape(venue)}"\n'


            if volume:
                md += f'volume: "{html_escape(volume)}"\n'
            if pages:
                md += f'pages: "{html_escape(pages)}"\n'


            md += f"category: {publist[pubsource]['category']}\n"


            if doi:
                md += f'doi: "{html_escape(doi)}"\n'
            if paperurl:
                md += f'paperurl: "{html_escape(paperurl)}"\n'


            md += f'authors_md: "{html_escape(authors_md)}"\n'
            md += f'citation: "{html_escape(citation_plain)}"\n'
            md += f'citation_md: "{html_escape(citation_md)}"\n'


            note = False
            if "note" in b.keys() and len(str(b["note"]).strip()) > 5:
                md += f'excerpt: "{html_escape(clean_text(b["note"]))}"\n'
                note = True


            md += "---\n"


            md += citation_md + "\n"


            if note:
                md += "\n" + clean_text(b["note"]) + "\n"



            md_filename = os.path.basename(md_filename)


            with open("../_publications/" + md_filename, "w", encoding="utf-8") as f:
                f.write(md)


            print(
                f'SUCCESSFULLY PARSED {bib_id}: "',
                title_clean[:60],
                "..." * (len(title_clean) > 60),
                '"'
            )


        except KeyError as e:
            fallback_title = clean_text(b.get("title", "Untitled"))
            print(
                f'WARNING Missing Expected Field {e} from entry {bib_id}: "',
                fallback_title[:30],
                "..." * (len(fallback_title) > 30),
                '"'
            )
            continue