from backend.matching.author_matcher import (
    calculate_match_score,
    classify_match
)


def build_unified_candidates(
    search_name: str,
    openalex_data: dict,
    semantic_data: dict,
    crossref_data: dict
) -> list:

    candidates = []

    search_author = {
        "name": search_name
    }

    # -------------------------
    # OpenAlex
    # -------------------------

    for author in openalex_data.get(
        "results",
        []
    ):

        affiliations = []

        for item in author.get(
            "affiliations",
            []
        ):

            institution = item.get(
                "institution",
                {}
            )

            if institution.get(
                "display_name"
            ):
                affiliations.append(
                    institution.get(
                        "display_name"
                    )
                )

        normalized_author = {
            "name": author.get(
                "display_name"
            ),
            "orcid": author.get(
                "orcid"
            ),
            "affiliations": affiliations
        }

        score = calculate_match_score(
            search_author,
            normalized_author
        )

        if score == 0:
            continue

        candidates.append({
            "source": "OpenAlex",
            "id": author.get("id"),
            "name": author.get(
                "display_name"
            ),
            "orcid": author.get(
                "orcid"
            ),
            "affiliations": affiliations,
            "works_count": author.get(
                "works_count"
            ),
            "citation_count": author.get(
                "cited_by_count"
            ),
            "url": author.get("id"),
            "score": score,
            "match_status": classify_match(
                score
            )
        })

    # -------------------------
    # Semantic Scholar
    # -------------------------

    for author in semantic_data.get(
        "data",
        []
    ):

        normalized_author = {
            "name": author.get(
                "name"
            ),
            "orcid": author.get(
                "externalIds",
                {}
            ).get(
                "ORCID"
            ),
            "affiliations": author.get(
                "affiliations",
                []
            )
        }

        score = calculate_match_score(
            search_author,
            normalized_author
        )

        # Ignore candidates with
        # no matching evidence.
        if score == 0:
            continue

        candidates.append({
            "source": "Semantic Scholar",
            "id": author.get(
                "authorId"
            ),
            "name": author.get(
                "name"
            ),
            "orcid": normalized_author[
                "orcid"
            ],
            "affiliations": normalized_author[
                "affiliations"
            ],
            "works_count": author.get(
                "paperCount"
            ),
            "citation_count": author.get(
                "citationCount"
            ),
            "url": author.get(
                "url"
            ),
            "score": score,
            "match_status": classify_match(
                score
            )
        })

    # -------------------------
    # Crossref
    # -------------------------

    works = crossref_data.get(
        "message",
        {}
    ).get(
        "items",
        []
    )

    for work in works:

        authors = work.get(
            "author",
            []
        )

        for author in authors:

            given = author.get(
                "given",
                ""
            )

            family = author.get(
                "family",
                ""
            )

            author_name = (
                f"{given} {family}"
                .strip()
            )

            if not author_name:
                continue

            affiliations = [
                affiliation.get(
                    "name"
                )
                for affiliation in author.get(
                    "affiliation",
                    []
                )
                if affiliation.get(
                    "name"
                )
            ]

            normalized_author = {
                "name": author_name,
                "orcid": author.get(
                    "ORCID"
                ),
                "affiliations": affiliations
            }

            score = calculate_match_score(
                search_author,
                normalized_author
            )

            # Ignore unrelated Crossref authors.
            if score == 0:
                continue

            doi = work.get(
                "DOI"
            )

            candidates.append({
                "source": "Crossref",
                "id": doi,
                "name": author_name,
                "orcid": author.get(
                    "ORCID"
                ),
                "affiliations": affiliations,
                "works_count": None,
                "citation_count": None,
                "url": (
                    f"https://doi.org/{doi}"
                    if doi
                    else None
                ),
                "score": score,
                "match_status": classify_match(
                    score
                )
            })

    # -------------------------
    # Sort by evidence score
    # -------------------------

    candidates.sort(
        key=lambda candidate: (
            candidate.get(
                "score",
                0
            ),
            candidate.get(
                "source",
                ""
            )
        ),
        reverse=True
    )

    return candidates