// ============================================================
// Researcher Metrics Dashboard
// FastAPI + PostgreSQL Connected
// ============================================================

const API_BASE = "https://researcher-profile-dashboard.onrender.com";

const appContent = document.getElementById("appContent");
const pageTitle = document.getElementById("pageTitle");
const pageSubtitle = document.getElementById("pageSubtitle");

const welcomeBtn = document.getElementById("welcomeBtn");
const dashboardBtn = document.getElementById("dashboardBtn");

const searchInput = document.getElementById("searchInput");
const researcherSelect =
    document.getElementById("researcherSelect");

const menuBtn = document.getElementById("menuBtn");

let researchers = [];
let currentResearcher = null;

let currentTab = "identity";

let currentPublications = [];


// ============================================================
// Welcome Page
// ============================================================

function showWelcome() {

    pageTitle.textContent =
        "Researcher Metrics Dashboard";

    pageSubtitle.textContent =
        "Bibliometric profile explorer";

    welcomeBtn.classList.add("active");
    dashboardBtn.classList.remove("active");

    appContent.innerHTML = `

        <section class="welcome-page">

            <div class="welcome-card">

                <span class="welcome-label">
                    BIBLIOMETRIC PROFILE EXPLORER
                </span>

                <h2>
                    Know a researcher's
                    impact at a glance
                </h2>

                <p>
                    Search any author to explore
                    publication activity, OpenAlex
                    information and research metrics
                    in one place.
                </p>

                <button
                    id="openDashboardBtn"
                    class="primary-btn"
                >
                    Open dashboard
                </button>

            </div>

            <div class="section-title">

                <h3>
                    What you can explore
                </h3>

                <p>
                    Research information organized
                    into six profile sections.
                </p>

            </div>

            <div class="feature-grid">

                <div class="feature-card">
                    <div class="feature-number">01</div>

                    <h3>Identity</h3>

                    <p>
                        Institution, researcher name,
                        author IDs and research field.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-number">02</div>

                    <h3>Publications</h3>

                    <p>
                        Publication count and
                        authorship activity.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-number">03</div>

                    <h3>OpenAlex</h3>

                    <p>
                        H-index, i10-index and
                        citation information.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-number">04</div>

                    <h3>Research Indices</h3>

                    <p>
                        Research impact indices
                        and their sources.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-number">05</div>

                    <h3>Author Roles</h3>

                    <p>
                        First-author and
                        corresponding-author metrics.
                    </p>
                </div>

                <div class="feature-card">
                    <div class="feature-number">06</div>

                    <h3>Classification</h3>

                    <p>
                        Researcher career
                        classification.
                    </p>
                </div>

            </div>

        </section>
    `;

    const openButton =
        document.getElementById("openDashboardBtn");

    if (openButton) {

        openButton.onclick = () => {
            searchInput.focus();
        };
    }
}


// ============================================================
// Search Researchers
// ============================================================

async function searchResearchers(name) {

    name = name.trim();

    if (!name) {

        researchers = [];
        currentResearcher = null;

        updateResearcherSelector();
        showWelcome();

        return;
    }

    try {

        const response = await fetch(
            `${API_BASE}/authors/search?name=${encodeURIComponent(name)}`
        );

        if (!response.ok) {

            throw new Error(
                `FastAPI returned ${response.status}`
            );
        }

        const data =
            await response.json();

        console.log(
            "FastAPI response:",
            data
        );


        // ====================================================
        // Researcher found in PostgreSQL
        // ====================================================

        if (data.researcher) {

            const r = data.researcher;

            const m =
                data.metrics || {};

            const i =
                data.indices || {};

            const roles =
            data.author_role_metrics ||
            data.roles ||
            {};

            researchers = [
                {

                    // ----------------------------------------
                    // Identity
                    // ----------------------------------------

                    id:
                        r.id,

                    name:
                        r.name ||
                        "Unknown",

                    institution:
                        r.institution ||
                        "Not available",

                    field:
                        r.core_field ||
                        "Not available",

                    institutionAuthorId:
                        r.institution_author_id ||
                        "Not available",

                    openAlexId:
                        r.openalex_author_id ||
                        "Not available",

                    semanticScholarId:
                        r.semantic_scholar_author_id ||
                        "Not available",


                    // ----------------------------------------
                    // Researcher Metrics
                    // ----------------------------------------

                    publicationCount:
                        m.total_papers ??
                        0,

                    papersAuthorsGt5:
                        m.papers_authors_gt_5 ??
                        null,

                    hIndex:
                        m.openalex_h_index ??
                        null,

                    i10Index:
                        m.openalex_i10_index ??
                        null,

                    citations:
                        m.openalex_total_citations ??
                        null,

                    yearsActive:
                        m.years_active ??
                        null,

                    firstYear:
                        m.first_year_of_publication ??
                        null,

                    firstAuthorPapers:
                        m.first_author_papers ??
                        null,

                    correspondingAuthorPapers:
                        m.corresponding_author_papers ??
                        null,

                    firstOrCorresponding:
                        m.first_or_corresponding_papers ??
                        null,


                    // ----------------------------------------
                    // Classification
                    // ----------------------------------------

                    classification:
                    m.bracket ?? null,


                    // ----------------------------------------
                    // Complete metric objects
                    // ----------------------------------------

                    metrics:
                        m,

                    indices:
                        i,

                    roles:
                        roles

                }
            ];


            currentResearcher =
                researchers[0];

            updateResearcherSelector();

            showResearcherDashboard(
                currentResearcher
            );

            return;
        }


        // ====================================================
        // API Candidates
        // ====================================================

        if (
            Array.isArray(data.candidates) &&
            data.candidates.length > 0
        ) {

            researchers =
                data.candidates.map(
                    (r, index) => {

                        const m =
                            r.metrics || {};

                        const i =
                            r.indices || {};

                        const roles =
                            r.author_role_metrics ||
                            r.roles ||
                            {};


                        return {

                            id:
                                r.id ??
                                index,

                            name:
                                r.name ||
                                "Unknown",

                            institution:
                                r.institution ||
                                "Not available",

                            field:
                                r.core_field ||
                                "Not available",

                            institutionAuthorId:
                                r.institution_author_id ||
                                "Not available",

                            openAlexId:
                                r.openalex_author_id ||
                                "Not available",

                            semanticScholarId:
                                r.semantic_scholar_author_id ||
                                "Not available",


                            publicationCount:
                                m.total_papers ??
                                r.publication_count ??
                                0,

                            papersAuthorsGt5:
                                m.papers_authors_gt_5 ??
                                r.papers_authors_gt_5 ??
                                null,

                            hIndex:
                                m.openalex_h_index ??
                                r.h_index ??
                                r.hIndex ??
                                null,

                            i10Index:
                                m.openalex_i10_index ??
                                r.i10_index ??
                                r.i10Index ??
                                null,

                            citations:
                                m.openalex_total_citations ??
                                r.citations ??
                                r.total_citations ??
                                null,

                            yearsActive:
                                m.years_active ??
                                r.years_active ??
                                r.yearsActive ??
                                null,

                            firstYear:
                                m.first_year_of_publication ??
                                r.first_year ??
                                r.firstYear ??
                                null,

                            firstAuthorPapers:
                                m.first_author_papers ??
                                r.first_author_papers ??
                                null,

                            correspondingAuthorPapers:
                                m.corresponding_author_papers ??
                                r.corresponding_author_papers ??
                                null,

                            firstOrCorresponding:
                                m.first_or_corresponding_papers ??
                                r.first_or_corresponding_papers ??
                                null,

                            classification:
                                r.classification ??
                                null,

                            metrics:
                                m,

                            indices:
                                i,

                            roles:
                                roles

                        };
                    }
                );


            currentResearcher =
                researchers[0];

            updateResearcherSelector();

            showResearcherDashboard(
                currentResearcher
            );

            return;
        }


        // ====================================================
        // No Researcher
        // ====================================================

        researchers = [];
        currentResearcher = null;

        updateResearcherSelector();

        showNoResearcher();

    }
    catch (error) {

        console.error(
            "FastAPI search error:",
            error
        );

        researchers = [];
        currentResearcher = null;

        updateResearcherSelector();

        showApiError();
    }
}


// ============================================================
// Researcher Selector
// ============================================================

function updateResearcherSelector() {

    researcherSelect.innerHTML = "";

    if (!researchers.length) {

        const option =
            document.createElement("option");

        option.value = "";

        option.textContent =
            "No researcher selected";

        researcherSelect.appendChild(option);

        return;
    }

    researchers.forEach(
        (researcher, index) => {

            const option =
                document.createElement("option");

            option.value =
                index;

            option.textContent =
                researcher.name;

            researcherSelect.appendChild(option);
        }
    );

    researcherSelect.value = "0";
}


// ============================================================
// Researcher Dashboard
// ============================================================

function showResearcherDashboard(
    researcher
) {

    currentResearcher = researcher;
    currentTab = "identity";

    pageTitle.textContent =
        "Researcher Dashboard";

    pageSubtitle.textContent =
        "Bibliometric profile explorer";

    welcomeBtn.classList.remove("active");
    dashboardBtn.classList.add("active");

    appContent.innerHTML = `

        <section class="researcher-profile">

            <div class="profile-header">

                <div>

                    <span class="welcome-label">
                        RESEARCHER PROFILE
                    </span>

                    <h2>
                        ${escapeHTML(
                            researcher.name
                        )}
                    </h2>

                    <p>
                        ${escapeHTML(
                            researcher.institution
                        )}

                        ${
                            researcher.field !==
                            "Not available"

                                ? " · " +
                                  escapeHTML(
                                      researcher.field
                                  )

                                : ""
                        }
                    </p>

                </div>

                <div
                    class="classification-badge"
                    id="classificationBadge"
                >
                    ${
                        researcher.classification ||
                        "Classification unavailable"
                    }
                </div>

            </div>


            <!-- Main Metrics -->

            <div class="profile-metrics">

                <div class="metric-card">

                    <span>
                        OpenAlex H-Index
                    </span>

                    <strong>
                        ${displayValue(
                            researcher.hIndex
                        )}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        i10-Index
                    </span>

                    <strong>
                        ${displayValue(
                            researcher.i10Index
                        )}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Total Citations
                    </span>

                    <strong>
                        ${formatNumber(
                            researcher.citations
                        )}
                    </strong>

                </div>


                <div class="metric-card">

                    <span>
                        Total Papers
                    </span>

                    <strong>
                        ${formatNumber(
                            researcher.publicationCount
                        )}
                    </strong>

                    <small class="metric-subtext">

                        ${
                            researcher.firstOrCorresponding !==
                            null

                                ? formatNumber(
                                      researcher.firstOrCorresponding
                                  ) +
                                  " first or corresponding"

                                : "—"
                        }

                    </small>

                </div>


                <div class="metric-card">

                    <span>
                        Years Active (Y)
                    </span>

                    <strong>
                        ${displayValue(
                            researcher.yearsActive
                        )}
                    </strong>

                    <small class="metric-subtext">

                        ${
                            researcher.firstYear
                                ? "since " +
                                  researcher.firstYear
                                : "—"
                        }

                    </small>

                </div>

            </div>


            <!-- Six Profile Sections -->

            <div class="profile-sections">

                <button
                    class="profile-section active"
                    data-section="identity"
                >
                    <span>01</span>

                    <strong>
                        Identity
                    </strong>

                    <small>
                        Institution, researcher ID
                        and author information
                    </small>
                </button>


                <button
                    class="profile-section"
                    data-section="publications"
                >
                    <span>02</span>

                    <strong>
                        Publications
                    </strong>

                    <small>
                        Publication counts and
                        authorship activity
                    </small>
                </button>


                <button
                    class="profile-section"
                    data-section="openalex"
                >
                    <span>03</span>

                    <strong>
                        OpenAlex
                    </strong>

                    <small>
                        OpenAlex profile and
                        citation information
                    </small>
                </button>


                <button
                    class="profile-section"
                    data-section="indices"
                >
                    <span>04</span>

                    <strong>
                        Research Indices
                    </strong>

                    <small>
                        Research impact indices
                        and their sources
                    </small>
                </button>


                <button
                    class="profile-section"
                    data-section="roles"
                >
                    <span>05</span>

                    <strong>
                        Author Roles
                    </strong>

                    <small>
                        First-author and
                        corresponding-author metrics
                    </small>
                </button>


                <button
                    class="profile-section"
                    data-section="classification"
                >
                    <span>06</span>

                    <strong>
                        Classification
                    </strong>

                    <small>
                        Researcher career
                        classification
                    </small>
                </button>

            </div>


            <div
                id="dashboardPage"
                class="section-details"
            ></div>

        </section>
    `;

    setupProfileSections();

    showDashboardTab("identity");
}


// ============================================================
// Profile Section Navigation
// ============================================================

function setupProfileSections() {

    document
        .querySelectorAll(".profile-section")
        .forEach(button => {

            button.onclick = () => {

                document
                    .querySelectorAll(".profile-section")
                    .forEach(item => {

                        item.classList.toggle(
                            "active",
                            item === button
                        );

                    });

                const section =
                    button.dataset.section;

                currentTab =
                    section;

                showDashboardTab(
                    section
                );
            };

        });
}


// ============================================================
// Show Selected Profile Section
// ============================================================

function showDashboardTab(tab) {

    const page =
        document.getElementById(
            "dashboardPage"
        );

    if (
        !page ||
        !currentResearcher
    ) {
        return;
    }

    switch (tab) {

        case "identity":

            renderIdentityPage(page);

            break;

        case "publications":

            renderPublicationsPage(page);

            break;

        case "openalex":

            renderOpenAlexPage(page);

            break;

        case "indices":

            renderIndicesPage(page);

            break;

        case "roles":

            renderRolesPage(page);

            break;

        case "classification":

            renderClassificationPage(page);

            break;
    }
}


// ============================================================
// Identity
// ============================================================

function renderIdentityPage(page) {

    const r =
        currentResearcher;

    page.innerHTML = `

        <h3>
            Identity
        </h3>

        <div class="details-grid">

            <div>
                <span>
                    Institution
                </span>

                <strong>
                    ${escapeHTML(
                        r.institution
                    )}
                </strong>
            </div>


            <div>
                <span>
                    ID
                </span>

                <strong>
                    ${escapeHTML(
                        String(r.id)
                    )}
                </strong>
            </div>


            <div>
                <span>
                    Author Name
                </span>

                <strong>
                    ${escapeHTML(
                        r.name
                    )}
                </strong>
            </div>


            <div>
                <span>
                    Core Field
                </span>

                <strong>
                    ${escapeHTML(
                        r.field
                    )}
                </strong>
            </div>


            <div>
                <span>
                    OpenAlex Author ID
                </span>

                <strong>
                    ${escapeHTML(
                        r.openAlexId
                    )}
                </strong>
            </div>


            <div>
                <span>
                    Semantic Scholar ID
                </span>

                <strong>
                    ${escapeHTML(
                        r.semanticScholarId
                    )}
                </strong>
            </div>


            <div>
                <span>
                    Institution Author ID
                </span>

                <strong>
                    ${escapeHTML(
                        r.institutionAuthorId
                    )}
                </strong>
            </div>

        </div>
    `;
}


// ============================================================
// Publications
// ============================================================

async function renderPublicationsPage(page) {

    const r =
        currentResearcher;

    page.innerHTML = `

        <h3>
            Publications
        </h3>

        <div class="profile-metrics">

            <div class="metric-card">

                <span>
                    First Year of Publication
                </span>

                <strong>
                    ${displayValue(
                        r.firstYear
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Total No. of Papers
                </span>

                <strong>
                    ${formatNumber(
                        r.publicationCount
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Papers with Authors &gt; 5
                </span>

                <strong>
                    ${displayValue(
                        r.papersAuthorsGt5
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    First Author Papers
                </span>

                <strong>
                    ${displayValue(
                        r.firstAuthorPapers
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Corresponding Author Papers
                </span>

                <strong>
                    ${displayValue(
                        r.correspondingAuthorPapers
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    First OR Corresponding
                </span>

                <strong>
                    ${displayValue(
                        r.firstOrCorresponding
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Years Active
                </span>

                <strong>
                    ${displayValue(
                        r.yearsActive
                    )}
                </strong>

            </div>

        </div>


        <p class="section-note">

            The metrics above come from the
            researcher record in PostgreSQL.

        </p>


        <div id="publicationList">

            <p class="section-note">
                Loading stored publication records...
            </p>

        </div>

    `;


    try {

        const response =
            await fetch(
                `${API_BASE}/authors/${encodeURIComponent(
                    r.id
                )}/publications`
            );

        if (!response.ok) {

            throw new Error(
                `Publication endpoint returned ${response.status}`
            );
        }

        const data =
            await response.json();

        currentPublications =
            Array.isArray(data)
                ? data
                : (
                    Array.isArray(
                        data.publications
                    )
                        ? data.publications
                        : []
                );

        renderPublicationList(
            currentPublications
        );

    }
    catch (error) {

        console.error(
            "Publication loading error:",
            error
        );

        const list =
            document.getElementById(
                "publicationList"
            );

        if (list) {

            list.innerHTML = `

                <p class="section-note">
                    Publication list could not
                    be loaded.
                </p>

            `;
        }
    }
}


// ============================================================
// Publication List
// ============================================================

function renderPublicationList(publications) {

    const list =
        document.getElementById(
            "publicationList"
        );

    if (!list) {
        return;
    }

    if (
        !Array.isArray(publications) ||
        publications.length === 0
    ) {

        list.innerHTML = `

            <p class="section-note">
                No stored publication records available yet.
            </p>

        `;

        return;
    }

    list.innerHTML = `

        <div class="publication-list">

            ${publications
                .map(
                    (publication, index) => {

                        const title =
                            publication.title ||
                            publication.work_title ||
                            "Untitled publication";

                        const year =
                            publication.year ||
                            publication.publication_year ||
                            publication.publicationYear ||
                            "—";

                        const doi =
                            publication.doi ||
                            "";

                        return `

                            <div
                                class="publication-item"
                            >

                                <span class="publication-number">
                                    ${index + 1}
                                </span>

                                <div>

                                    <strong>
                                        ${escapeHTML(
                                            title
                                        )}
                                    </strong>

                                    <small>
                                        ${escapeHTML(
                                            String(year)
                                        )}

                                        ${
                                            doi
                                                ? " · DOI: " +
                                                  escapeHTML(
                                                      doi
                                                  )
                                                : ""
                                        }
                                    </small>

                                </div>

                            </div>

                        `;
                    }
                )
                .join("")}

        </div>
    `;
}


// ============================================================
// OpenAlex
// ============================================================

function renderOpenAlexPage(page) {

    const r =
        currentResearcher;

    page.innerHTML = `

        <h3>
            OpenAlex
        </h3>

        <div class="details-grid">

            <div>

                <span>
                    OpenAlex Author ID
                </span>

                <strong>
                    ${escapeHTML(
                        r.openAlexId
                    )}
                </strong>

            </div>


            <div>

                <span>
                    H-Index
                </span>

                <strong>
                    ${displayValue(
                        r.hIndex
                    )}
                </strong>

            </div>


            <div>

                <span>
                    i10-Index
                </span>

                <strong>
                    ${displayValue(
                        r.i10Index
                    )}
                </strong>

            </div>


            <div>

                <span>
                    Total Citations
                </span>

                <strong>
                    ${formatNumber(
                        r.citations
                    )}
                </strong>

            </div>


            <div>

                <span>
                    Total Works
                </span>

                <strong>
                    ${formatNumber(
                        r.publicationCount
                    )}
                </strong>

            </div>


            <div>

                <span>
                    ORCID
                </span>

                <strong>
                    Not available
                </strong>

            </div>

        </div>


        <p class="section-note">

            OpenAlex information is connected
            through the researcher profile.

        </p>

    `;
}


// ============================================================
// Research Indices
// ============================================================

function renderIndicesPage(page) {

    const indices =
        currentResearcher.indices || {};

    const indexDefinitions = [

        [
            "m_quotient",
            "M-Quotient (M = h/Y)"
        ],

        [
            "hyperindex_m_quotient",
            "HyperIndex (M-Quotient)"
        ],

        [
            "ar_index",
            "AR-Index"
        ],

        [
            "hyperindex_ar_index",
            "HyperIndex (AR-Index)"
        ],

        [
            "local_h_index",
            "Local H-Index"
        ],

        [
            "g_index",
            "g-index"
        ],

        [
            "a_index",
            "A-index"
        ],

        [
            "r_index",
            "r-index"
        ],

        [
            "h2_index",
            "h(2)-index"
        ],

        [
            "hg_index",
            "hg-index"
        ],

        [
            "m_index",
            "m-index"
        ],

        [
            "q2_index",
            "q2-index"
        ],

        [
            "e_index",
            "e-index"
        ],

        [
            "hw_index",
            "hw-index"
        ],

        [
            "sh_index",
            "Sh-index"
        ]

    ];


    page.innerHTML = `

        <h3>
            Research Indices
        </h3>

        <div class="indices-grid">

            ${
                indexDefinitions
                    .map(
                        ([key, label]) => {

                            const value =
                                getMetricValue(
                                    indices,
                                    key
                                );

                            return `

                                <div
                                    class="metric-card index-card"
                                >

                                    <span>
                                        ${escapeHTML(
                                            label
                                        )}
                                    </span>

                                    <strong>
                                        ${displayValue(
                                            value
                                        )}
                                    </strong>

                                    <small class="metric-subtext">
                                        PostgreSQL
                                    </small>

                                </div>

                            `;
                        }
                    )
                    .join("")
            }

        </div>

        <p class="section-note">

            Research impact indices stored
            in PostgreSQL.

        </p>

    `;
}


// ============================================================
// Author Roles
// ============================================================

function renderRolesPage(page) {

    const r =
        currentResearcher;

    const roles =
        r.roles || {};

    page.innerHTML = `

        <h3>
            Author Roles
        </h3>

        <div class="profile-metrics">

            <div class="metric-card">

                <span>
                    First Author Papers
                </span>

                <strong>
                    ${displayValue(
                        r.firstAuthorPapers
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Corresponding Author Papers
                </span>

                <strong>
                    ${displayValue(
                        r.correspondingAuthorPapers
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    First OR Corresponding
                </span>

                <strong>
                    ${displayValue(
                        r.firstOrCorresponding
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Papers with Authors &gt; 5
                </span>

                <strong>
                    ${displayValue(
                        r.papersAuthorsGt5
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    First Author H-Index
                </span>

                <strong>
                    ${displayValue(
                        roles.first_author_h_index
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Second Author H-Index
                </span>

                <strong>
                    ${displayValue(
                        roles.second_author_h_index
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Co-Author H-Index
                </span>

                <strong>
                    ${displayValue(
                        roles.co_author_h_index
                    )}
                </strong>

            </div>


            <div class="metric-card">

                <span>
                    Corresponding Author H-Index
                </span>

                <strong>
                    ${displayValue(
                        roles.corresponding_author_h_index
                    )}
                </strong>

            </div>

        </div>


        <p class="section-note">

            These values describe the
            researcher's authorship role
            metrics stored in PostgreSQL.

        </p>

    `;
}


// ============================================================
// Classification
// ============================================================

function renderClassificationPage(page) {

    const r =
        currentResearcher;

    page.innerHTML = `

        <h3>
            Classification
        </h3>

        <div class="single-detail">

            <span>
                Researcher Classification
            </span>

            <strong>
                ${
                    r.classification ||
                    "Classification unavailable"
                }
            </strong>

        </div>

        <p class="section-note">

            Career-stage classification is not
            currently provided by the database
            response.

        </p>

    `;
}


// ============================================================
// No Researcher
// ============================================================

function showNoResearcher() {

    pageTitle.textContent =
        "Researcher Dashboard";

    pageSubtitle.textContent =
        "No researcher found";

    welcomeBtn.classList.remove("active");
    dashboardBtn.classList.add("active");

    appContent.innerHTML = `

        <section class="empty-dashboard">

            <div class="empty-icon">
                🔎
            </div>

            <h2>
                No researcher found
            </h2>

            <p>
                Try another researcher name.
            </p>

        </section>
    `;
}


// ============================================================
// API Error
// ============================================================

function showApiError() {

    pageTitle.textContent =
        "Researcher Dashboard";

    pageSubtitle.textContent =
        "FastAPI connection problem";

    appContent.innerHTML = `

        <section class="empty-dashboard">

            <div class="empty-icon">
                ⚠
            </div>

            <h2>
                Could not connect to FastAPI
            </h2>

            <p>
                Make sure the FastAPI server
                is running at 127.0.0.1:8000.
            </p>

        </section>
    `;
}


// ============================================================
// Search Input
// ============================================================

let searchTimer;

searchInput.addEventListener(
    "input",
    event => {

        clearTimeout(searchTimer);

        const value =
            event.target.value.trim();

        if (!value) {

            researchers = [];
            currentResearcher = null;

            updateResearcherSelector();
            showWelcome();

            return;
        }

        searchTimer =
            setTimeout(
                () => {

                    searchResearchers(
                        value
                    );

                },
                400
            );
    }
);


// ============================================================
// Researcher Selector
// ============================================================

researcherSelect.addEventListener(
    "change",
    event => {

        const index =
            Number(
                event.target.value
            );

        if (
            Number.isNaN(index) ||
            !researchers[index]
        ) {
            return;
        }

        currentResearcher =
            researchers[index];

        showResearcherDashboard(
            currentResearcher
        );
    }
);


// ============================================================
// Navigation
// ============================================================

welcomeBtn.onclick = () => {

    showWelcome();

};


dashboardBtn.onclick = () => {

    if (currentResearcher) {

        showResearcherDashboard(
            currentResearcher
        );

    }
    else {

        showDashboardEmpty();

    }

};


// ============================================================
// Empty Dashboard
// ============================================================

function showDashboardEmpty() {

    pageTitle.textContent =
        "Researcher Dashboard";

    pageSubtitle.textContent =
        "Select a researcher to view their profile";

    welcomeBtn.classList.remove("active");
    dashboardBtn.classList.add("active");

    appContent.innerHTML = `

        <section class="empty-dashboard">

            <div class="empty-icon">
                🔎
            </div>

            <h2>
                No researcher selected
            </h2>

            <p>
                Search for a researcher using
                the search box in the sidebar.
            </p>

        </section>
    `;
}


// ============================================================
// Mobile Menu
// ============================================================

menuBtn.onclick = () => {

    document
        .querySelector(".sidebar")
        .classList.toggle("open");

};


// ============================================================
// Utility: Escape HTML
// ============================================================

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "—";
    }

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


// ============================================================
// Utility: Format Number
// ============================================================

function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "—";
    }

    const number =
        Number(value);

    if (
        Number.isNaN(number)
    ) {

        return "—";
    }

    return number.toLocaleString();
}


// ============================================================
// Utility: Display Value
// ============================================================

function displayValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "—";
    }

    return escapeHTML(value);
}


// ============================================================
// Utility: Metric Value
// ============================================================

function getMetricValue(
    metrics,
    key
) {

    if (
        !metrics ||
        typeof metrics !== "object"
    ) {

        return null;
    }

    if (
        Object.prototype.hasOwnProperty.call(
            metrics,
            key
        )
    ) {

        return metrics[key];
    }

    return null;
}


// ============================================================
// Initial Load
// ============================================================

showWelcome();