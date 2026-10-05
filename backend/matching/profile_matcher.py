from backend.matching.author_matcher import (
    calculate_match_score,
    classify_match
)


def build_candidate_match(
    target_author: dict,
    candidate: dict,
    source: str
) -> dict:
    """
    Calculate the match score and classification
    for one candidate author.
    """

    score = calculate_match_score(
        target_author,
        candidate
    )

    return {
        "source": source,
        "score": score,
        "match_status": classify_match(score),
        "candidate": candidate
    }


def match_candidates(
    target_author: dict,
    candidates: list,
    source: str
) -> list:
    """
    Calculate match score and status for multiple candidates.
    """

    results = []

    for candidate in candidates:

        result = build_candidate_match(
            target_author,
            candidate,
            source
        )

        results.append(result)

    return results


def match_openalex_authors(
    target_name: str,
    openalex_response: dict
) -> list:
    """
    Match candidates returned by OpenAlex.
    """

    candidates = openalex_response.get(
        "results",
        []
    )

    target_author = {
        "display_name": target_name
    }

    return match_candidates(
        target_author,
        candidates,
        "openalex"
    )


def match_semantic_scholar_authors(
    target_name: str,
    semantic_response: dict
) -> list:
    """
    Match candidates returned by Semantic Scholar.
    """

    candidates = semantic_response.get(
        "data",
        []
    )

    target_author = {
        "name": target_name
    }

    return match_candidates(
        target_author,
        candidates,
        "semantic_scholar"
    )


def match_crossref_authors(
    target_name: str,
    crossref_response: dict
) -> list:
    """
    Match works returned by Crossref.
    """

    works = crossref_response.get(
        "message",
        {}
    ).get(
        "items",
        []
    )

    target_author = {
        "name": target_name
    }

    results = []

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

            author_name = f"{given} {family}".strip()

            if not author_name:
                continue

            candidate = {
                "name": author_name,
                "work": work
            }

            matched = match_candidates(
                target_author,
                [candidate],
                "crossref"
            )

            results.extend(matched)

    return results