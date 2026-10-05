import re


def normalize_doi(doi):
    if not doi:
        return None

    doi = doi.strip().lower()

    doi = doi.replace(
        "https://doi.org/",
        ""
    )

    doi = doi.replace(
        "http://doi.org/",
        ""
    )

    doi = doi.replace(
        "doi:",
        ""
    )

    return doi.strip()


def normalize_title(title):
    if not title:
        return ""

    title = title.lower()

    title = re.sub(
        r"[^\w\s]",
        " ",
        title
    )

    title = " ".join(
        title.split()
    )

    return title


def titles_match(title1, title2):
    title1 = normalize_title(title1)
    title2 = normalize_title(title2)

    if not title1 or not title2:
        return False

    return title1 == title2


def years_match(year1, year2):
    if not year1 or not year2:
        return False

    try:
        return int(year1) == int(year2)

    except (ValueError, TypeError):
        return False


def authors_overlap(
    authors1,
    authors2
):
    """
    Check whether publication author names overlap.
    """

    names1 = {
        normalize_title(
            author.get("name")
        )
        for author in authors1
        if author.get("name")
    }

    names2 = {
        normalize_title(
            author.get("name")
        )
        for author in authors2
        if author.get("name")
    }

    names1.discard("")
    names2.discard("")

    return bool(
        names1.intersection(names2)
    )


def publications_match(
    publication1,
    publication2
):
    """
    Determine whether two publication
    records likely represent the same work.
    """

    doi1 = normalize_doi(
        publication1.get("doi")
    )

    doi2 = normalize_doi(
        publication2.get("doi")
    )

    # ------------------------------------------------
    # LEVEL 1 — DOI
    # ------------------------------------------------

    if doi1 and doi2:

        if doi1 == doi2:
            return {
                "matched": True,
                "method": "doi"
            }

    # ------------------------------------------------
    # LEVEL 2 — TITLE + YEAR
    # ------------------------------------------------

    title_match = titles_match(
        publication1.get("title"),
        publication2.get("title")
    )

    year_match = years_match(
        publication1.get("publication_year"),
        publication2.get("publication_year")
    )

    if title_match and year_match:

        return {
            "matched": True,
            "method": "title_year"
        }

    # ------------------------------------------------
    # LEVEL 3 — TITLE + AUTHOR OVERLAP
    # ------------------------------------------------

    if title_match:

        author_match = authors_overlap(
            publication1.get("authors", []),
            publication2.get("authors", [])
        )

        if author_match:

            return {
                "matched": True,
                "method": "title_authors"
            }

    return {
        "matched": False,
        "method": None
    }