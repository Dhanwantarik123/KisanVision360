// =========================================================
// KISANVISION360+ GOVERNMENT SCHEME INTELLIGENCE
// =========================================================

"use strict";


// =========================================================
// GLOBAL CONFIG
// =========================================================

const GOVERNMENT_CONFIG = {

    searchDelay: 180,

    animationDelay: 45,

    language:
        document.documentElement.lang ||
        localStorage.getItem("kisanvision360_language") ||
        "en"

};


// =========================================================
// DOM ELEMENTS
// =========================================================

let searchInput = null;
let schemeContainer = null;
let schemeCount = null;

let selectedCategory = "all";

let searchTimer = null;


// =========================================================
// INITIALIZE
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        searchInput =
            document.getElementById(
                "searchInput"
            );

        schemeContainer =
            document.getElementById(
                "schemeContainer"
            );

        schemeCount =
            document.getElementById(
                "schemeCount"
            );


        initializeGovernmentSchemes();

    }
);


// =========================================================
// INITIALIZE GOVERNMENT SCHEMES
// =========================================================

function initializeGovernmentSchemes() {

    setupSearch();

    setupFilterButtons();

    setupSchemeCards();

    applyFilters();

    console.log(
        "🏛️ KisanVision360+ Government Scheme Intelligence loaded."
    );

}


// =========================================================
// SEARCH
// =========================================================

function setupSearch() {

    if (!searchInput) {
        return;
    }


    searchInput.addEventListener(
        "input",
        function () {

            clearTimeout(
                searchTimer
            );


            searchTimer =
                setTimeout(
                    function () {

                        applyFilters();

                    },
                    GOVERNMENT_CONFIG.searchDelay
                );

        }
    );


    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Escape"
            ) {

                searchInput.value = "";

                applyFilters();

                searchInput.focus();

            }

        }
    );

}


// =========================================================
// FILTER BUTTONS
// =========================================================

function setupFilterButtons() {

    document
        .querySelectorAll(
            ".filter-btn"
        )
        .forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        const category =
                            this.dataset.category ||
                            this.getAttribute(
                                "data-filter"
                            ) ||
                            "all";


                        filterSchemes(
                            category,
                            this
                        );

                    }
                );

            }
        );

}


// =========================================================
// FILTER SCHEMES
// =========================================================

function filterSchemes(
    category,
    button
) {

    selectedCategory =
        String(
            category || "all"
        )
        .toLowerCase()
        .trim();


    document
        .querySelectorAll(
            ".filter-btn"
        )
        .forEach(
            function (btn) {

                btn.classList.remove(
                    "active"
                );

                btn.setAttribute(
                    "aria-pressed",
                    "false"
                );

            }
        );


    if (button) {

        button.classList.add(
            "active"
        );

        button.setAttribute(
            "aria-pressed",
            "true"
        );

    }


    applyFilters();

}


// =========================================================
// APPLY FILTERS
// =========================================================

function applyFilters() {

    if (!schemeContainer) {
        return;
    }


    const searchText =
        searchInput
            ? searchInput.value
                .toLowerCase()
                .trim()
            : "";


    const cards =
        schemeContainer.querySelectorAll(
            ".scheme-card"
        );


    let visibleCount = 0;


    cards.forEach(
        function (card, index) {

            const searchableText =
                getCardSearchText(
                    card
                );


            const category =
                getCardCategory(
                    card
                );


            const matchesCategory =
                selectedCategory === "all" ||
                category === selectedCategory ||
                searchableText.includes(
                    selectedCategory
                );


            const matchesSearch =
                searchText === "" ||
                searchableText.includes(
                    searchText
                );


            const visible =
                matchesCategory &&
                matchesSearch;


            if (visible) {

                card.style.display = "";

                card.classList.remove(
                    "scheme-hidden"
                );

                card.classList.add(
                    "scheme-visible"
                );


                card.style.animationDelay =
                    `${index * GOVERNMENT_CONFIG.animationDelay}ms`;


                visibleCount++;

            }

            else {

                card.style.display =
                    "none";

                card.classList.remove(
                    "scheme-visible"
                );

                card.classList.add(
                    "scheme-hidden"
                );

            }

        }
    );


    updateSchemeCount(
        visibleCount
    );


    handleEmptyState(
        visibleCount
    );


    updateSearchStatus(
        visibleCount,
        cards.length
    );

}


// =========================================================
// GET SEARCHABLE CARD TEXT
// =========================================================

function getCardSearchText(card) {

    if (!card) {
        return "";
    }


    const explicitName =
        card.dataset.name ||
        "";


    const explicitCategory =
        card.dataset.category ||
        "";


    const text =
        card.textContent ||
        "";


    return (

        explicitName +
        " " +
        explicitCategory +
        " " +
        text

    )
        .toLowerCase()
        .replace(
            /\s+/g,
            " "
        )
        .trim();

}


// =========================================================
// GET CARD CATEGORY
// =========================================================

function getCardCategory(card) {

    if (!card) {
        return "";
    }


    return (

        card.dataset.category ||
        ""

    )
        .toLowerCase()
        .trim();

}


// =========================================================
// UPDATE SCHEME COUNT
// =========================================================

function updateSchemeCount(
    count
) {

    if (!schemeCount) {
        return;
    }


    if (count === 1) {

        schemeCount.textContent =
            "1 Scheme";

    }

    else {

        schemeCount.textContent =
            `${count} Schemes`;

    }


    schemeCount.setAttribute(
        "aria-live",
        "polite"
    );

}


// =========================================================
// EMPTY STATE
// =========================================================

function handleEmptyState(
    visibleCount
) {

    if (!schemeContainer) {
        return;
    }


    let emptyState =
        document.getElementById(
            "schemeEmptyState"
        );


    if (visibleCount > 0) {

        if (emptyState) {

            emptyState.remove();

        }

        return;

    }


    if (!emptyState) {

        emptyState =
            document.createElement(
                "div"
            );


        emptyState.id =
            "schemeEmptyState";


        emptyState.className =
            "scheme-empty-state";


        emptyState.innerHTML = `

            <div class="empty-icon">
                🔎
            </div>

            <h3>
                No matching schemes found
            </h3>

            <p>
                Try another search term or select a different category.
            </p>

            <button
                type="button"
                class="clear-scheme-search"
                id="clearSchemeSearch"
            >
                Clear Filters
            </button>

        `;


        schemeContainer.appendChild(
            emptyState
        );


        const clearButton =
            emptyState.querySelector(
                "#clearSchemeSearch"
            );


        if (clearButton) {

            clearButton.addEventListener(
                "click",
                clearFilters
            );

        }

    }

}


// =========================================================
// CLEAR FILTERS
// =========================================================

function clearFilters() {

    if (searchInput) {

        searchInput.value = "";

    }


    selectedCategory =
        "all";


    document
        .querySelectorAll(
            ".filter-btn"
        )
        .forEach(
            function (button) {

                button.classList.remove(
                    "active"
                );

                button.setAttribute(
                    "aria-pressed",
                    "false"
                );


                const category =
                    button.dataset.category ||
                    button.dataset.filter;


                if (
                    !category ||
                    category.toLowerCase() ===
                    "all"
                ) {

                    button.classList.add(
                        "active"
                    );

                    button.setAttribute(
                        "aria-pressed",
                        "true"
                    );

                }

            }
        );


    applyFilters();

}


// =========================================================
// SEARCH STATUS
// =========================================================

function updateSearchStatus(
    visibleCount,
    totalCount
) {

    const status =
        document.getElementById(
            "schemeSearchStatus"
        );


    if (!status) {
        return;
    }


    if (totalCount === 0) {

        status.textContent =
            "No schemes available.";

        return;

    }


    if (visibleCount === totalCount) {

        status.textContent =
            `Showing all ${totalCount} schemes.`;

        return;

    }


    status.textContent =
        `Showing ${visibleCount} of ${totalCount} schemes.`;

}


// =========================================================
// SCHEME CARDS
// =========================================================

function setupSchemeCards() {

    document
        .querySelectorAll(
            ".scheme-card"
        )
        .forEach(
            function (card) {

                card.addEventListener(
                    "mouseenter",
                    function () {

                        this.classList.add(
                            "scheme-card-hover"
                        );

                    }
                );


                card.addEventListener(
                    "mouseleave",
                    function () {

                        this.classList.remove(
                            "scheme-card-hover"
                        );

                    }
                );

            }
        );

}


// =========================================================
// SHOW SCHEME DETAILS
// =========================================================

function showSchemeDetails(
    button
) {

    if (!button) {
        return;
    }


    const card =
        button.closest(
            ".scheme-card"
        );


    if (!card) {
        return;
    }


    const name =
        getText(
            card.querySelector(
                "h2, h3, .scheme-name"
            )
        ) ||
        card.dataset.name ||
        "Government Scheme";


    const category =
        getCardCategory(
            card
        ) ||
        "General";


    const department =
        getText(
            card.querySelector(
                ".department, .scheme-department"
            )
        );


    const purpose =
        getText(
            card.querySelector(
                ".purpose, .scheme-purpose"
            )
        );


    const eligibility =
        getText(
            card.querySelector(
                ".eligibility, .scheme-eligibility"
            )
        );


    const link =
        card.querySelector(
            "a[href]"
        );


    const officialLink =
        link
            ? link.href
            : "";


    showSchemeModal({

        name:
            name,

        category:
            category,

        department:
            department,

        purpose:
            purpose,

        eligibility:
            eligibility,

        link:
            officialLink

    });

}


// =========================================================
// TEXT HELPER
// =========================================================

function getText(element) {

    if (!element) {
        return "";
    }


    return (
        element.textContent ||
        ""
    )
        .replace(
            /\s+/g,
            " "
        )
        .trim();

}


// =========================================================
// SCHEME MODAL
// =========================================================

function showSchemeModal(
    scheme
) {

    let modal =
        document.getElementById(
            "schemeDetailsModal"
        );


    if (modal) {

        modal.remove();

    }


    modal =
        document.createElement(
            "div"
        );


    modal.id =
        "schemeDetailsModal";


    modal.className =
        "scheme-modal";


    modal.setAttribute(
        "role",
        "dialog"
    );


    modal.setAttribute(
        "aria-modal",
        "true"
    );


    modal.setAttribute(
        "aria-label",
        "Government scheme details"
    );


    const officialButton =
        scheme.link
            ? `
                <a
                    href="${escapeAttribute(scheme.link)}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="scheme-official-btn"
                >
                    🌐 Open Official Portal
                </a>
              `
            : "";


    modal.innerHTML = `

        <div class="scheme-modal-overlay"></div>

        <div class="scheme-modal-content">

            <button
                type="button"
                class="scheme-modal-close"
                aria-label="Close"
            >
                ×
            </button>

            <div class="scheme-modal-icon">
                🏛️
            </div>

            <span class="scheme-modal-category">
                ${escapeHTML(scheme.category)}
            </span>

            <h2>
                ${escapeHTML(scheme.name)}
            </h2>

            ${
                scheme.department
                ? `
                    <div class="scheme-modal-row">
                        <strong>Department</strong>
                        <span>
                            ${escapeHTML(
                                scheme.department
                            )}
                        </span>
                    </div>
                  `
                : ""
            }

            ${
                scheme.purpose
                ? `
                    <div class="scheme-modal-section">
                        <h4>Purpose</h4>
                        <p>
                            ${escapeHTML(
                                scheme.purpose
                            )}
                        </p>
                    </div>
                  `
                : ""
            }

            ${
                scheme.eligibility
                ? `
                    <div class="scheme-modal-section">
                        <h4>Eligibility</h4>
                        <p>
                            ${escapeHTML(
                                scheme.eligibility
                            )}
                        </p>
                    </div>
                  `
                : ""
            }

            <div class="scheme-modal-notice">

                ℹ️ Eligibility, benefits, deadlines and
                application requirements should be verified
                on the official government portal.

            </div>

            <div class="scheme-modal-actions">

                ${officialButton}

                <button
                    type="button"
                    class="scheme-modal-cancel"
                >
                    Close
                </button>

            </div>

        </div>

    `;


    document.body.appendChild(
        modal
    );


    requestAnimationFrame(
        function () {

            modal.classList.add(
                "active"
            );

        }
    );


    const closeButton =
        modal.querySelector(
            ".scheme-modal-close"
        );


    const cancelButton =
        modal.querySelector(
            ".scheme-modal-cancel"
        );


    const overlay =
        modal.querySelector(
            ".scheme-modal-overlay"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeSchemeModal
        );

    }


    if (cancelButton) {

        cancelButton.addEventListener(
            "click",
            closeSchemeModal
        );

    }


    if (overlay) {

        overlay.addEventListener(
            "click",
            closeSchemeModal
        );

    }


    document.addEventListener(
        "keydown",
        handleModalEscape
    );


    if (closeButton) {

        closeButton.focus();

    }

}


// =========================================================
// CLOSE SCHEME MODAL
// =========================================================

function closeSchemeModal() {

    const modal =
        document.getElementById(
            "schemeDetailsModal"
        );


    if (!modal) {
        return;
    }


    modal.classList.remove(
        "active"
    );


    setTimeout(
        function () {

            if (
                modal &&
                modal.parentNode
            ) {

                modal.remove();

            }

        },
        250
    );


    document.removeEventListener(
        "keydown",
        handleModalEscape
    );

}


// =========================================================
// ESCAPE KEY
// =========================================================

function handleModalEscape(
    event
) {

    if (
        event.key === "Escape"
    ) {

        closeSchemeModal();

    }

}


// =========================================================
// SAFE HTML ESCAPING
// =========================================================

function escapeHTML(value) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(value ?? "");


    return div.innerHTML;

}


// =========================================================
// SAFE ATTRIBUTE ESCAPING
// =========================================================

function escapeAttribute(value) {

    return String(value ?? "")
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#39;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        );

}


// =========================================================
// GLOBAL API
// =========================================================

window.KisanVisionGovernment = {

    filterSchemes:
        filterSchemes,

    applyFilters:
        applyFilters,

    clearFilters:
        clearFilters,

    showSchemeDetails:
        showSchemeDetails,

    closeSchemeModal:
        closeSchemeModal

};


// =========================================================
// END
// =========================================================

console.log(
    "🏛️ KisanVision360+ Government Scheme JS ready."
);