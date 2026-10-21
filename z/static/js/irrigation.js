// =========================================================
// KISANVISION360+ SMART IRRIGATION
// Weather-Aware • Soil-Aware • Crop-Aware
// =========================================================

"use strict";


// =========================================================
// CONFIGURATION
// =========================================================

const IRRIGATION_CONFIG = {

    maxCropLength: 100,

    maxRainfall: 10000,

    animationDuration: 600,

    language:
        document.documentElement.lang ||
        localStorage.getItem("kisanvision360_language") ||
        "en"

};


// =========================================================
// DOM READY
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeIrrigation();

    }
);


// =========================================================
// INITIALIZE
// =========================================================

function initializeIrrigation() {

    animateCards();

    setupFormValidation();

    setupIrrigationInputs();

    initializeProgressBars();

    setupLoadingButton();

    initializeClock();

    initializeWeatherAwareness();

    initializeSmoothScroll();

    calculateSuggestion();

    console.log(
        "💧 KisanVision360+ Smart Irrigation loaded."
    );

}


// =========================================================
// CARD ANIMATION
// =========================================================

function animateCards() {

    const cards =
        document.querySelectorAll(
            ".card, .form-card, .ai-card, .result-card, .irrigation-card"
        );


    cards.forEach(
        function (card, index) {

            card.classList.add(
                "irrigation-card-ready"
            );


            card.style.animationDelay =
                `${index * 100}ms`;

        }
    );

}


// =========================================================
// FORM VALIDATION
// =========================================================

function setupFormValidation() {

    const form =
        document.querySelector(
            "form"
        );


    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        function (event) {

            const crop =
                document.querySelector(
                    "input[name='crop']"
                );


            const rainfall =
                document.querySelector(
                    "input[name='rainfall']"
                );


            if (
                crop &&
                crop.value.trim() === ""
            ) {

                event.preventDefault();

                showIrrigationMessage(
                    "Please enter the crop name.",
                    "error"
                );

                crop.focus();

                return;

            }


            if (
                crop &&
                crop.value.trim().length >
                IRRIGATION_CONFIG.maxCropLength
            ) {

                event.preventDefault();

                showIrrigationMessage(
                    "Crop name is too long.",
                    "error"
                );

                crop.focus();

                return;

            }


            if (rainfall) {

                const value =
                    parseFloat(
                        rainfall.value
                    );


                if (
                    Number.isNaN(value) ||
                    value < 0
                ) {

                    event.preventDefault();

                    showIrrigationMessage(
                        "Rainfall cannot be negative.",
                        "error"
                    );

                    rainfall.focus();

                    return;

                }


                if (
                    value >
                    IRRIGATION_CONFIG.maxRainfall
                ) {

                    event.preventDefault();

                    showIrrigationMessage(
                        "Please enter a valid rainfall value.",
                        "error"
                    );

                    rainfall.focus();

                    return;

                }

            }

        }
    );

}


// =========================================================
// INPUT LISTENERS
// =========================================================

function setupIrrigationInputs() {

    const crop =
        document.querySelector(
            "input[name='crop']"
        );


    const soil =
        document.querySelector(
            "select[name='soil']"
        );


    const rainfall =
        document.querySelector(
            "input[name='rainfall']"
        );


    const inputs = [
        crop,
        soil,
        rainfall
    ];


    inputs.forEach(
        function (element) {

            if (!element) {
                return;
            }


            element.addEventListener(
                "input",
                calculateSuggestion
            );


            element.addEventListener(
                "change",
                calculateSuggestion
            );

        }
    );

}


// =========================================================
// AI / SMART IRRIGATION SUGGESTION
// =========================================================

function calculateSuggestion() {

    const crop =
        document.querySelector(
            "input[name='crop']"
        );


    const soil =
        document.querySelector(
            "select[name='soil']"
        );


    const rain =
        document.querySelector(
            "input[name='rainfall']"
        );


    if (!crop) {
        return;
    }


    updateRecommendation();

}


// =========================================================
// UPDATE RECOMMENDATION
// =========================================================

function updateRecommendation() {

    const soilElement =
        document.querySelector(
            "select[name='soil']"
        );


    const rainElement =
        document.querySelector(
            "input[name='rainfall']"
        );


    const cropElement =
        document.querySelector(
            "input[name='crop']"
        );


    const soil =
        soilElement
            ? soilElement.value
                .toLowerCase()
                .trim()
            : "normal";


    const rainfall =
        rainElement
            ? parseFloat(
                rainElement.value
            ) || 0
            : 0;


    const crop =
        cropElement
            ? cropElement.value
                .trim()
            : "";


    // -------------------------------------------------
    // IMPORTANT:
    // This is a FRONTEND advisory heuristic.
    // Actual irrigation recommendation should come
    // from backend/weather/farm data.
    // -------------------------------------------------

    let message =
        "Enter farm information to generate an irrigation advisory.";

    let duration =
        "Not calculated";

    let water =
        "Unknown";

    let level =
        "normal";

    let score =
        50;


    // -------------------------------------------------
    // RAINFALL INTELLIGENCE
    // -------------------------------------------------

    if (rainfall > 50) {

        message =
            "Recent rainfall is high. Irrigation may not be required immediately.";

        duration =
            "0 min";

        water =
            "Very Low";

        level =
            "low";

        score =
            15;

    }

    else if (rainfall >= 20) {

        message =
            "Moderate rainfall detected. Check soil moisture before irrigation.";

        duration =
            "10–15 min*";

        water =
            "Low";

        level =
            "low";

        score =
            30;

    }

    // -------------------------------------------------
    // SOIL INTELLIGENCE
    // -------------------------------------------------

    else if (
        soil === "dry" ||
        soil === "very dry"
    ) {

        message =
            "Soil appears dry. Irrigation may be required soon.";

        duration =
            "25–35 min*";

        water =
            "High";

        level =
            "high";

        score =
            80;

    }

    else if (
        soil === "normal" ||
        soil === "moist"
    ) {

        message =
            "Soil condition appears suitable. Use moderate irrigation if crop moisture is low.";

        duration =
            "15–20 min*";

        water =
            "Medium";

        level =
            "medium";

        score =
            55;

    }

    else if (
        soil === "wet"
    ) {

        message =
            "Soil appears wet. Avoid unnecessary irrigation and monitor moisture.";

        duration =
            "0–10 min*";

        water =
            "Low";

        level =
            "low";

        score =
            25;

    }


    // -------------------------------------------------
    // NO CROP
    // -------------------------------------------------

    if (!crop) {

        message =
            "Enter the crop name for a more relevant irrigation advisory.";

    }


    updateRecommendationCards(
        message,
        duration,
        water,
        score,
        level
    );


    updateIrrigationInsight(
        rainfall,
        soil,
        crop
    );

}


// =========================================================
// UPDATE RECOMMENDATION CARDS
// =========================================================

function updateRecommendationCards(
    message,
    duration,
    water,
    score,
    level
) {

    const recommend =
        document.querySelectorAll(
            ".recommend"
        );


    if (recommend.length >= 1) {

        recommend[0].innerHTML = `

            <strong>
                Recommendation
            </strong>

            <br>

            ${escapeHTML(message)}

        `;

    }


    if (recommend.length >= 2) {

        recommend[1].innerHTML = `

            <strong>
                Advisory Duration
            </strong>

            <br>

            ${escapeHTML(duration)}

        `;

    }


    if (recommend.length >= 3) {

        recommend[2].innerHTML = `

            <strong>
                Water Requirement
            </strong>

            <br>

            ${escapeHTML(water)}

        `;

    }


    // Optional additional elements

    const scoreElement =
        document.querySelector(
            "[data-irrigation-score]"
        );


    if (scoreElement) {

        scoreElement.textContent =
            `${Math.round(score)}%`;

    }


    const levelElement =
        document.querySelector(
            "[data-irrigation-level]"
        );


    if (levelElement) {

        levelElement.textContent =
            formatLevel(level);

        levelElement.dataset.level =
            level;

    }

}


// =========================================================
// FARM IRRIGATION INSIGHT
// =========================================================

function updateIrrigationInsight(
    rainfall,
    soil,
    crop
) {

    const insight =
        document.querySelector(
            "[data-irrigation-insight]"
        );


    if (!insight) {
        return;
    }


    let text =
        "Monitor soil moisture and weather conditions before irrigation.";


    if (rainfall > 50) {

        text =
            "🌧️ Rainfall is significant. Check field moisture before adding more water.";

    }

    else if (
        soil === "dry" ||
        soil === "very dry"
    ) {

        text =
            "💧 Soil is dry. Inspect crop moisture and irrigation infrastructure before watering.";

    }

    else if (
        soil === "wet"
    ) {

        text =
            "🌱 Soil is wet. Avoid unnecessary watering to reduce waterlogging risk.";

    }

    else if (crop) {

        text =
            `🌾 Monitor ${crop} moisture regularly and adjust irrigation according to actual field conditions.`;

    }


    insight.textContent =
        text;

}


// =========================================================
// FORMAT LEVEL
// =========================================================

function formatLevel(level) {

    const levels = {

        low:
            "Low",

        medium:
            "Medium",

        high:
            "High",

        normal:
            "Normal"

    };


    return (
        levels[level] ||
        "Normal"
    );

}


// =========================================================
// PROGRESS ANIMATION
// =========================================================

function initializeProgressBars() {

    const statValues =
        document.querySelectorAll(
            ".card h2, [data-progress]"
        );


    statValues.forEach(
        function (stat) {

            const rawText =
                stat.textContent.trim();


            if (
                !rawText.includes("%")
            ) {

                return;

            }


            const target =
                parseFloat(
                    rawText.replace(
                        /[^0-9.-]/g,
                        ""
                    )
                );


            if (
                Number.isNaN(target) ||
                target < 0 ||
                target > 100
            ) {

                return;

            }


            stat.textContent =
                "0%";


            animatePercentage(
                stat,
                target
            );

        }
    );

}


// =========================================================
// ANIMATE PERCENTAGE
// =========================================================

function animatePercentage(
    element,
    target
) {

    const duration =
        1000;


    const startTime =
        performance.now();


    function update(
        currentTime
    ) {

        const progress =
            Math.min(
                (
                    currentTime -
                    startTime
                ) /
                duration,
                1
            );


        const eased =
            1 -
            Math.pow(
                1 - progress,
                3
            );


        const value =
            Math.round(
                target *
                eased
            );


        element.textContent =
            `${value}%`;


        if (
            progress < 1
        ) {

            requestAnimationFrame(
                update
            );

        }

    }


    requestAnimationFrame(
        update
    );

}


// =========================================================
// SUBMIT BUTTON
// =========================================================

function setupLoadingButton() {

    const form =
        document.querySelector(
            "form"
        );


    if (!form) {
        return;
    }


    const submitBtn =
        form.querySelector(
            "button[type='submit'], input[type='submit']"
        );


    if (!submitBtn) {
        return;
    }


    form.addEventListener(
        "submit",
        function () {

            // Do not block submission.
            // Only change UI.

            submitBtn.disabled =
                true;


            if (
                submitBtn.tagName
                    .toLowerCase() ===
                "button"
            ) {

                submitBtn.innerHTML =
                    '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

            }

            else {

                submitBtn.value =
                    "Processing...";

            }

        }
    );

}


// =========================================================
// LIVE CLOCK
// =========================================================

function initializeClock() {

    updateIrrigationClock();


    setInterval(
        updateIrrigationClock,
        1000
    );

}


function updateIrrigationClock() {

    const clock =
        document.getElementById(
            "liveClock"
        );


    if (!clock) {
        return;
    }


    const date =
        new Date();


    try {

        clock.textContent =
            date.toLocaleTimeString(
                "en-IN",
                {
                    hour:
                        "2-digit",

                    minute:
                        "2-digit",

                    second:
                        "2-digit"
                }
            );

    }

    catch (error) {

        clock.textContent =
            date.toLocaleTimeString();

    }

}


// =========================================================
// WEATHER AWARENESS
// =========================================================

function initializeWeatherAwareness() {

    const hero =
        document.querySelector(
            ".hero"
        );


    if (!hero) {
        return;
    }


    const hour =
        new Date().getHours();


    // Do not overwrite CSS background.
    // Add a class instead.

    if (
        hour >= 18 ||
        hour < 6
    ) {

        hero.classList.add(
            "irrigation-night"
        );

    }

    else {

        hero.classList.add(
            "irrigation-day"
        );

    }

}


// =========================================================
// SMOOTH SCROLL
// =========================================================

function initializeSmoothScroll() {

    document
        .querySelectorAll(
            "a[href^='#']"
        )
        .forEach(
            function (anchor) {

                anchor.addEventListener(
                    "click",
                    function (event) {

                        const href =
                            this.getAttribute(
                                "href"
                            );


                        if (
                            !href ||
                            href === "#"
                        ) {

                            return;

                        }


                        const target =
                            document.querySelector(
                                href
                            );


                        if (!target) {
                            return;
                        }


                        event.preventDefault();


                        target.scrollIntoView(
                            {
                                behavior:
                                    "smooth",
                                block:
                                    "start"
                            }
                        );

                    }
                );

            }
        );

}


// =========================================================
// NOTIFICATION / MESSAGE
// =========================================================

function showIrrigationMessage(
    message,
    type = "info"
) {

    // Use existing dashboard notification
    // if available.

    if (
        typeof window
            .KisanVisionDashboard
            ?.showNotification ===
        "function"
    ) {

        window.KisanVisionDashboard
            .showNotification(
                message,
                type
            );

        return;

    }


    // Fallback

    console[type === "error"
        ? "error"
        : "log"](
        message
    );


    // Do not use unsafe innerHTML.

    const existing =
        document.getElementById(
            "irrigationMessage"
        );


    if (existing) {

        existing.textContent =
            message;

        existing.classList.add(
            "show"
        );

        return;

    }


    const div =
        document.createElement(
            "div"
        );


    div.id =
        "irrigationMessage";


    div.className =
        `irrigation-message ${type}`;


    div.textContent =
        message;


    document.body.appendChild(
        div
    );


    setTimeout(
        function () {

            div.classList.remove(
                "show"
            );

        },
        3500
    );

}


// =========================================================
// HTML ESCAPE
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
// PUBLIC API
// =========================================================

window.KisanVisionIrrigation = {

    calculateSuggestion:
        calculateSuggestion,

    updateRecommendation:
        updateRecommendation,

    refresh:
        calculateSuggestion,

    showMessage:
        showIrrigationMessage

};


// =========================================================
// END
// =========================================================

console.log(
    "💧 KisanVision360+ Smart Irrigation JS ready."
);