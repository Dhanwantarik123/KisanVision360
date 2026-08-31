const searchInput = document.getElementById("searchInput");
const schemeContainer = document.getElementById("schemeContainer");
const schemeCount = document.getElementById("schemeCount");

let selectedCategory = "all";


function filterSchemes(category, button) {

    selectedCategory = category;

    document.querySelectorAll(".filter-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    if (button) {
        button.classList.add("active");
    }

    applyFilters();
}


function applyFilters() {

    const searchText =
        searchInput.value.toLowerCase().trim();

    const cards =
        document.querySelectorAll(".scheme-card");

    let visibleCount = 0;

    cards.forEach(card => {

        const category =
            card.dataset.category;

        const name =
            card.dataset.name;

        const matchesCategory =
            selectedCategory === "all" ||
            category === selectedCategory;

        const matchesSearch =
            name.includes(searchText) ||
            category.toLowerCase().includes(searchText);

        if (matchesCategory && matchesSearch) {

            card.style.display = "";

            visibleCount++;

        } else {

            card.style.display = "none";

        }

    });

    if (schemeCount) {

        schemeCount.textContent =
            visibleCount + (visibleCount === 1 ? " Scheme" : " Schemes");

    }
}


if (searchInput) {

    searchInput.addEventListener(
        "input",
        applyFilters
    );

}


function showSchemeDetails(button) {

    const card =
        button.closest(".scheme-card");

    const name =
        card.querySelector("h2").textContent;

    const category =
        card.dataset.category;

    alert(
        "Scheme: " +
        name +
        "\nCategory: " +
        category +
        "\n\nFor complete eligibility and application information, visit the Official Portal."
    );

}