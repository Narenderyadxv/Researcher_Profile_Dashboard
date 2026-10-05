import re


def normalize_name(name: str) -> str:
    """
    Normalize an author's name for comparison.
    """

    if not name:
        return ""

    name = str(name).lower().strip()

    # Convert:
    # "Einstein, Albert" -> "Albert Einstein"
    if "," in name:

        parts = [
            part.strip()
            for part in name.split(",")
        ]

        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"

    # Remove punctuation
    name = re.sub(
        r"[^\w\s]",
        " ",
        name
    )

    # Remove extra spaces
    name = " ".join(
        name.split()
    )

    return name


def names_match(name1: str, name2: str) -> bool:
    """
    Check whether two author names are reasonably compatible.
    """

    name1 = normalize_name(name1)
    name2 = normalize_name(name2)

    if not name1 or not name2:
        return False

    # Exact match
    if name1 == name2:
        return True

    parts1 = name1.split()
    parts2 = name2.split()

    if not parts1 or not parts2:
        return False

    # Last names must match
    if parts1[-1] != parts2[-1]:
        return False

    # Same number of name parts:
    # "Manisha Goel" <-> "M Goel"
    if len(parts1) == len(parts2):

        for part1, part2 in zip(
            parts1[:-1],
            parts2[:-1]
        ):

            if not part1 or not part2:
                return False

            if part1 == part2:
                continue

            if part1[0] == part2[0]:
                continue

            return False

        return True

    # Allow:
    # "Manisha Goel" <-> "M Goel"
    if len(parts1) > 1 and len(parts2) == 2:

        if parts1[-1] == parts2[-1]:

            first_initial = parts1[0][0]
            candidate_initial = parts2[0][0]

            return first_initial == candidate_initial

    if len(parts2) > 1 and len(parts1) == 2:

        if parts1[-1] == parts2[-1]:

            first_initial = parts2[0][0]
            candidate_initial = parts1[0][0]

            return first_initial == candidate_initial

    return False


def find_name_matches(
    target_name: str,
    candidates: list
) -> list:
    """
    Find candidate authors whose names match the target name.
    """

    matches = []

    for candidate in candidates:

        candidate_name = (
            candidate.get("display_name")
            or candidate.get("name")
        )

        if candidate_name and names_match(
            target_name,
            candidate_name
        ):
            matches.append(candidate)

    return matches


def normalize_orcid(orcid: str) -> str:
    """
    Normalize an ORCID identifier.
    """

    if not orcid:
        return ""

    orcid = str(orcid).strip().lower()

    orcid = orcid.replace(
        "https://orcid.org/",
        ""
    )

    orcid = orcid.replace(
        "http://orcid.org/",
        ""
    )

    return orcid.strip()


def orcids_match(
    orcid1: str,
    orcid2: str
) -> bool:
    """
    Check whether two ORCID identifiers match.
    """

    orcid1 = normalize_orcid(orcid1)
    orcid2 = normalize_orcid(orcid2)

    if not orcid1 or not orcid2:
        return False

    return orcid1 == orcid2


def normalize_affiliation(
    affiliation: str
) -> str:
    """
    Normalize an institution/affiliation name.
    """

    if not affiliation:
        return ""

    affiliation = str(
        affiliation
    ).lower()

    affiliation = re.sub(
        r"[^\w\s]",
        " ",
        affiliation
    )

    affiliation = " ".join(
        affiliation.split()
    )

    return affiliation


def affiliations_match(
    author1: dict,
    author2: dict
) -> bool:
    """
    Check whether two author records have
    compatible affiliations.
    """

    affiliations1 = author1.get(
        "affiliations",
        []
    )

    affiliations2 = author2.get(
        "affiliations",
        []
    )

    if not affiliations1 or not affiliations2:
        return False

    normalized1 = {
        normalize_affiliation(
            affiliation
        )
        for affiliation in affiliations1
        if affiliation
    }

    normalized2 = {
        normalize_affiliation(
            affiliation
        )
        for affiliation in affiliations2
        if affiliation
    }

    normalized1.discard("")
    normalized2.discard("")

    if not normalized1 or not normalized2:
        return False

    # Exact normalized institution match
    if normalized1.intersection(
        normalized2
    ):
        return True

    return False


def authors_match(
    author1: dict,
    author2: dict
) -> bool:
    """
    Determine whether two author records likely
    represent the same author.

    This function is intentionally conservative.
    A name match alone does not guarantee identity.
    """

    name1 = (
        author1.get("display_name")
        or author1.get("name")
    )

    name2 = (
        author2.get("display_name")
        or author2.get("name")
    )

    orcid1 = author1.get("orcid")
    orcid2 = author2.get("orcid")

    # ORCID is strong evidence
    if orcid1 and orcid2:

        if orcids_match(
            orcid1,
            orcid2
        ):
            return True

        # Different ORCIDs mean we should
        # not treat them as the same person.
        return False

    # Fall back to name compatibility
    if name1 and name2:

        return names_match(
            name1,
            name2
        )

    return False


def calculate_match_score(
    author1: dict,
    author2: dict
) -> int:
    """
    Calculate evidence-based matching score.

    Score components:

    ORCID match       = +50
    Exact name        = +20
    Abbreviated name  = +10
    Affiliation match = +15

    Important:
    A name-only match remains below the threshold
    for a strong identity decision.
    """

    score = 0

    name1 = (
        author1.get("display_name")
        or author1.get("name")
    )

    name2 = (
        author2.get("display_name")
        or author2.get("name")
    )

    orcid1 = author1.get("orcid")
    orcid2 = author2.get("orcid")

    # -------------------------
    # ORCID
    # -------------------------

    if (
        orcid1
        and orcid2
        and orcids_match(
            orcid1,
            orcid2
        )
    ):
        score += 50

    # -------------------------
    # Name
    # -------------------------

    if name1 and name2:

        normalized1 = normalize_name(
            name1
        )

        normalized2 = normalize_name(
            name2
        )

        if normalized1 == normalized2:

            score += 20

        elif names_match(
            name1,
            name2
        ):

            score += 10

    # -------------------------
    # Affiliation
    # -------------------------

    if affiliations_match(
        author1,
        author2
    ):
        score += 15

    return score


def classify_match(score: int) -> str:
    """
    Classify a match based on available evidence.

    These labels describe evidence strength;
    they do not automatically establish identity.
    """

    if score >= 70:
        return "Strong match"

    if score >= 35:
        return "Possible match"

    if score >= 20:
        return "Name match"

    return "Uncertain"