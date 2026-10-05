def clean_doi(doi):
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


def merge_group(publications):
    """
    Merge multiple records that represent
    the same publication.
    """

    if not publications:
        raise ValueError(
            "Publication group cannot be empty"
        )

    # Start with the first record
    merged = dict(publications[0])

    # Clean DOI
    for publication in publications:
        doi = clean_doi(
            publication.get("doi")
        )

        if doi:
            merged["doi"] = doi
            break

    # Collect sources
    sources = {}

    for publication in publications:
        source = publication.get("source")
        source_id = publication.get("source_id")

        if source:
            sources[source] = source_id

    merged["sources"] = sources

    # Keep citations from every source
    citations_by_source = {}

    for publication in publications:
        source = publication.get("source")
        citation_count = publication.get(
            "citation_count"
        )

        if (
            source
            and citation_count is not None
        ):
            citations_by_source[source] = citation_count

    merged["citations_by_source"] = (
        citations_by_source
    )

    # Prefer OpenAlex citation count
    if "openalex" in citations_by_source:
        merged["citation_count"] = (
            citations_by_source["openalex"]
        )
    elif citations_by_source:
        merged["citation_count"] = next(
            iter(citations_by_source.values())
        )
    else:
        merged["citation_count"] = None

    # Prefer the longest author list
    publications_with_authors = [
        p for p in publications
        if p.get("authors")
    ]

    if publications_with_authors:
        best = max(
            publications_with_authors,
            key=lambda p: len(p.get("authors", []))
        )

        merged["authors"] = best["authors"]
        merged["authors_source"] = best.get(
            "source"
        )

    # Prefer Crossref title when available
    for publication in publications:
        if (
            publication.get("source")
            == "crossref"
            and publication.get("title")
        ):
            merged["title"] = publication["title"]
            break

    # Preserve venue if available
    for publication in publications:
        if publication.get("venue"):
            merged["venue"] = publication["venue"]
            break

    # Preserve publisher if available
    for publication in publications:
        if publication.get("publisher"):
            merged["publisher"] = publication["publisher"]
            break

    # Check for conflicts
    conflicts = []

    years = {
        p.get("publication_year")
        for p in publications
        if p.get("publication_year") is not None
    }

    if len(years) > 1:
        conflicts.append({
            "field": "publication_year",
            "values": list(years)
        })

    merged["conflicts"] = conflicts
    merged["needs_review"] = bool(conflicts)

    return merged