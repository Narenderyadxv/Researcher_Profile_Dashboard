def normalize_openalex_work(work: dict) -> dict:
    """
    Convert one OpenAlex work into our common
    publication structure.
    """

    authors = []

    for position, authorship in enumerate(
        work.get("authorships", []),
        start=1
    ):

        author = authorship.get("author", {})

        institutions = []

        for institution in authorship.get(
            "institutions",
            []
        ):
            name = institution.get("display_name")

            if name:
                institutions.append(name)

        authors.append({
            "name": author.get("display_name"),
            "source_author_id": author.get("id"),
            "orcid": author.get("orcid"),
            "position": position,
            "institutions": institutions,
            "is_corresponding": authorship.get(
                "is_corresponding",
                False
            )
        })

    venue = None

    primary_location = work.get(
        "primary_location"
    )

    if primary_location:

        source = primary_location.get(
            "source"
        )

        if source:
            venue = source.get(
                "display_name"
            )

    return {
        "title": work.get("title"),
        "publication_year": work.get(
            "publication_year"
        ),
        "publication_date": work.get(
            "publication_date"
        ),
        "doi": work.get("doi"),
        "publication_type": work.get("type"),
        "venue": venue,
        "publisher": None,
        "citation_count": work.get(
            "cited_by_count"
        ),

        "authors": authors,

        "openalex_work_id": (
            work.get("id", "").replace(
                "https://openalex.org/",
                ""
            )
            if work.get("id")
            else None
        ),

        "semantic_scholar_paper_id": None,

        "crossref_doi": None
    }


def normalize_semantic_paper(paper: dict) -> dict:
    """
    Convert one Semantic Scholar paper
    into our common publication structure.
    """

    authors = []

    for position, author in enumerate(
        paper.get("authors", []),
        start=1
    ):

        authors.append({
            "name": author.get("name"),
            "source_author_id": author.get(
                "authorId"
            ),
            "orcid": None,
            "position": position,
            "institutions": [],
            "is_corresponding": False
        })

    external_ids = paper.get(
        "externalIds"
    ) or {}

    doi = external_ids.get(
        "DOI"
    )

    return {
        "title": paper.get("title"),
        "publication_year": paper.get(
            "year"
        ),
        "publication_date": paper.get(
            "publicationDate"
        ),
        "doi": doi,
        "publication_type": None,
        "venue": paper.get("venue"),
        "publisher": None,
        "citation_count": paper.get(
            "citationCount"
        ),

        "authors": authors,

        "openalex_work_id": None,

        "semantic_scholar_paper_id": paper.get(
            "paperId"
        ),

        "crossref_doi": None
    }


def normalize_crossref_work(work: dict) -> dict:
    """
    Convert one Crossref work into our common
    publication structure.
    """

    authors = []

    for position, author in enumerate(
        work.get("author", []),
        start=1
    ):

        affiliations = []

        for affiliation in author.get(
            "affiliation",
            []
        ):
            name = affiliation.get("name")

            if name:
                affiliations.append(name)

        full_name = " ".join(
            part
            for part in [
                author.get("given"),
                author.get("family")
            ]
            if part
        )

        authors.append({
            "name": full_name,
            "source_author_id": None,
            "orcid": author.get("ORCID"),
            "position": position,
            "affiliations": affiliations,
            "is_corresponding": False
        })

    published = work.get(
        "published"
    ) or {}

    date_parts = published.get(
        "date-parts",
        []
    )

    publication_year = None
    publication_date = None

    if date_parts and date_parts[0]:

        parts = date_parts[0]

        publication_year = parts[0]

        publication_date = "-".join(
            str(part)
            for part in parts
        )

    doi = work.get("DOI")

    return {
        "title": (
            work.get("title", [None])[0]
        ),

        "publication_year": publication_year,

        "publication_date": publication_date,

        "doi": doi,

        "publication_type": work.get(
            "type"
        ),

        "venue": (
            work.get(
                "container-title",
                [None]
            )[0]
        ),

        "publisher": work.get(
            "publisher"
        ),

        "citation_count": work.get(
            "is-referenced-by-count"
        ),

        "authors": authors,

        "openalex_work_id": None,

        "semantic_scholar_paper_id": None,

        "crossref_doi": doi
    }