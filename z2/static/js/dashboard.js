// =========================================================
// KISANVISION360+ DASHBOARD JAVASCRIPT
// Smart Farming Command Center
// =========================================================

"use strict";


// =========================================================
// CONFIGURATION
// =========================================================

const DASHBOARD_CONFIG = {

    weatherRefresh: 600000, // 10 minutes

    notificationDuration: 4000,

    animationDuration: 1500,

    language:
        document.documentElement.lang ||
        localStorage.getItem("kisanvision360_language") ||
        "en"

};


// =========================================================
// DOM READY
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeDashboard();

});


// =========================================================
// INITIALIZE DASHBOARD
// =========================================================

function initializeDashboard() {

    updateClock();

    initializeCardHover();

    initializeSidebar();

    initializeCounters();

    initializeScrollAnimations();

    initializeSmoothScroll();

    initializeTheme();

    initializeDashboardButtons();

    initializeWeatherRefresh();

    updateDashboardDate();

    console.log(
        "🌱 KisanVision360+ Dashboard loaded successfully."
    );

}


// =========================================================
// LIVE CLOCK
// =========================================================

function updateClock() {

    const clock =
        document.getElementById("clock");


    if (!clock) {
        return;
    }


    const now = new Date();


    const options = {

        weekday: "short",

        year: "numeric",

        month: "short",

        day: "numeric",

        hour: "2-digit",

        minute: "2-digit",

        second: "2-digit"

    };


    try {

        clock.textContent =
            now.toLocaleString(
                "en-IN",
                options
            );

    }

    catch (error) {

        clock.textContent =
            now.toLocaleString();

    }

}


// Update every second

setInterval(
    updateClock,
    1000
);


// =========================================================
// DASHBOARD DATE
// =========================================================

function updateDashboardDate() {

    const elements =
        document.querySelectorAll(
            "[data-dashboard-date]"
        );


    if (!elements.length) {
        return;
    }


    const date =
        new Date();


    elements.forEach(function (element) {

        try {

            element.textContent =
                date.toLocaleDateString(
                    "en-IN",
                    {
                        weekday: "long",
                        day: "numeric",
                        month: "long",
                        year: "numeric"
                    }
                );

        }

        catch (error) {

            element.textContent =
                date.toDateString();

        }

    });

}


// =========================================================
// CARD HOVER
// =========================================================

function initializeCardHover() {

    const cards =
        document.querySelectorAll(
            ".card, .analytics-card, .dashboard-card"
        );


    cards.forEach(function (card) {

        card.addEventListener(
            "mouseenter",
            function () {

                if (
                    window.innerWidth >
                    768
                ) {

                    card.classList.add(
                        "dashboard-hover"
                    );

                }

            }
        );


        card.addEventListener(
            "mouseleave",
            function () {

                card.classList.remove(
                    "dashboard-hover"
                );

            }
        );

    });

}


// =========================================================
// ACTIVE SIDEBAR MENU
// =========================================================

function initializeSidebar() {

    const menuItems =
        document.querySelectorAll(
            ".sidebar li, .kv-sidebar li"
        );


    if (!menuItems.length) {
        return;
    }


    const currentPath =
        window.location.pathname;


    menuItems.forEach(function (item) {

        const link =
            item.querySelector("a");


        if (!link) {
            return;
        }


        const href =
            link.getAttribute("href");


        if (
            href &&
            href !== "#" &&
            currentPath === href
        ) {

            item.classList.add(
                "active"
            );

        }


        item.addEventListener(
            "click",
            function () {

                menuItems.forEach(
                    function (menu) {

                        menu.classList.remove(
                            "active"
                        );

                    }
                );


                item.classList.add(
                    "active"
                );

            }
        );

    });

}


// =========================================================
// COUNTER ANIMATION
// =========================================================

function initializeCounters() {

    const counters =
        document.querySelectorAll(
            "[data-counter]"
        );


    counters.forEach(function (element) {

        const target =
            parseFloat(
                element.dataset.counter
            );


        if (
            Number.isNaN(target)
        ) {

            return;

        }


        const suffix =
            element.dataset.suffix ||
            "";


        animateNumber(
            element,
            0,
            target,
            DASHBOARD_CONFIG.animationDuration,
            suffix
        );

    });


    // Compatibility with old progress bar

    const health =
        document.querySelector(
            ".progress-bar"
        );


    if (health) {

        let text =
            health.textContent.trim();


        let value =
            parseFloat(
                text.replace(
                    /[^0-9.-]/g,
                    ""
                )
            );


        if (
            !Number.isNaN(value) &&
            value >= 0 &&
            value <= 100
        ) {

            health.textContent =
                "0%";


            animateNumber(
                health,
                0,
                value,
                DASHBOARD_CONFIG.animationDuration,
                "%"
            );

        }

    }

}


// =========================================================
// GENERIC NUMBER ANIMATION
// =========================================================

function animateNumber(
    element,
    start,
    end,
    duration,
    suffix = ""
) {

    if (!element) {
        return;
    }


    if (start === end) {

        element.textContent =
            Math.round(end) +
            suffix;

        return;

    }


    const startTime =
        performance.now();


    function update(currentTime) {

        const elapsed =
            currentTime -
            startTime;


        const progress =
            Math.min(
                elapsed / duration,
                1
            );


        // Ease-out animation

        const eased =
            1 -
            Math.pow(
                1 - progress,
                3
            );


        const value =
            start +
            (end - start) *
            eased;


        if (
            Number.isInteger(end)
        ) {

            element.textContent =
                Math.round(value) +
                suffix;

        }

        else {

            element.textContent =
                value.toFixed(1) +
                suffix;

        }


        if (progress < 1) {

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
// WEATHER REFRESH
// =========================================================

function initializeWeatherRefresh() {

    const weatherElement =
        document.querySelector(
            "[data-weather-city]"
        );


    if (!weatherElement) {

        console.log(
            "ℹ️ Weather auto-refresh skipped on this page."
        );

        return;

    }


    setInterval(
        refreshWeather,
        DASHBOARD_CONFIG.weatherRefresh
    );

}


// =========================================================
// REFRESH WEATHER
// =========================================================

async function refreshWeather() {

    const weatherElement =
        document.querySelector(
            "[data-weather-city]"
        );


    if (!weatherElement) {
        return;
    }


    const city =
        weatherElement.dataset.weatherCity;


    if (!city) {
        return;
    }


    try {

        const response =
            await fetch(
                `/weather/${encodeURIComponent(city)}`,
                {
                    method: "GET",
                    headers: {
                        "Accept":
                            "application/json"
                    },
                    credentials:
                        "same-origin"
                }
            );


        if (!response.ok) {

            throw new Error(
                `Weather HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        updateWeatherElements(
            data
        );


        console.log(
            "🌤️ Weather updated successfully."
        );


    }

    catch (error) {

        console.warn(
            "Weather update failed:",
            error
        );

    }

}


// =========================================================
// UPDATE WEATHER ELEMENTS
// =========================================================

function updateWeatherElements(data) {

    if (!data) {
        return;
    }


    const mappings = {

        temperature:
            ["#temp", "[data-weather='temperature']"],

        feels_like:
            ["#feelsLike", "[data-weather='feels_like']"],

        humidity:
            ["#humidity", "[data-weather='humidity']"],

        wind:
            ["#wind", "[data-weather='wind']"],

        pressure:
            ["#pressure", "[data-weather='pressure']"],

        rainfall:
            ["#rainfall", "[data-weather='rainfall']"],

        clouds:
            ["#clouds", "[data-weather='clouds']"],

        visibility:
            ["#visibility", "[data-weather='visibility']"],

        description:
            ["#weatherDescription", "[data-weather='description']"]

    };


    Object.keys(mappings).forEach(
        function (key) {

            const selectors =
                mappings[key];


            let element = null;


            for (
                let i = 0;
                i < selectors.length;
                i++
            ) {

                element =
                    document.querySelector(
                        selectors[i]
                    );


                if (element) {
                    break;
                }

            }


            if (
                element &&
                data[key] !== undefined &&
                data[key] !== null
            ) {

                element.textContent =
                    data[key];

            }

        }
    );

}


// =========================================================
// DASHBOARD NOTIFICATION
// =========================================================

function showNotification(
    message,
    type = "info"
) {

    if (!message) {
        return;
    }


    const div =
        document.createElement("div");


    div.className =
        "notification-popup " +
        `notification-${type}`;


    div.setAttribute(
        "role",
        "status"
    );


    div.setAttribute(
        "aria-live",
        "polite"
    );


    const content =
        document.createElement("div");


    content.className =
        "notification-popup-content";


    content.textContent =
        message;


    div.appendChild(
        content
    );


    const close =
        document.createElement("button");


    close.type =
        "button";


    close.className =
        "notification-close";


    close.setAttribute(
        "aria-label",
        "Close notification"
    );


    close.textContent =
        "×";


    close.addEventListener(
        "click",
        function () {

            removeNotification(
                div
            );

        }
    );


    div.appendChild(
        close
    );


    document.body.appendChild(
        div
    );


    requestAnimationFrame(
        function () {

            div.classList.add(
                "show"
            );

        }
    );


    const timer =
        setTimeout(
            function () {

                removeNotification(
                    div
                );

            },
            DASHBOARD_CONFIG.notificationDuration
        );


    div._notificationTimer =
        timer;

}


// =========================================================
// REMOVE NOTIFICATION
// =========================================================

function removeNotification(element) {

    if (!element) {
        return;
    }


    if (
        element._notificationTimer
    ) {

        clearTimeout(
            element._notificationTimer
        );

    }


    element.classList.remove(
        "show"
    );


    setTimeout(
        function () {

            if (
                element &&
                element.parentNode
            ) {

                element.remove();

            }

        },
        400
    );

}


// =========================================================
// WELCOME NOTIFICATION
// =========================================================

function showWelcomeNotification() {

    const alreadyShown =
        sessionStorage.getItem(
            "kisanvision360_welcome_shown"
        );


    if (alreadyShown) {
        return;
    }


    sessionStorage.setItem(
        "kisanvision360_welcome_shown",
        "true"
    );


    const language =
        DASHBOARD_CONFIG.language;


    const messages = {

        en:
            "🌾 Welcome to KisanVision360+ Dashboard",

        hi:
            "🌾 KisanVision360+ डैशबोर्ड में आपका स्वागत है",

        mr:
            "🌾 KisanVision360+ डॅशबोर्डमध्ये आपले स्वागत आहे",

        kn:
            "🌾 KisanVision360+ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸ್ವಾಗತ",

        te:
            "🌾 KisanVision360+ డ్యాష్‌బోర్డ్‌కు స్వాగతం",

        ta:
            "🌾 KisanVision360+ டாஷ்போர்டுக்கு வரவேற்கிறோம்"

    };


    showNotification(
        messages[language] ||
        messages.en,
        "success"
    );

}


// Show welcome after page is ready

document.addEventListener(
    "DOMContentLoaded",
    function () {

        setTimeout(
            showWelcomeNotification,
            700
        );

    }
);


// =========================================================
// SCROLL ANIMATIONS
// =========================================================

function initializeScrollAnimations() {

    const elements =
        document.querySelectorAll(
            ".card, .analytics-card, .dashboard-card, .section, .service-card"
        );


    if (!elements.length) {
        return;
    }


    // Browser does not support observer

    if (
        !("IntersectionObserver" in window)
    ) {

        elements.forEach(
            function (element) {

                element.classList.add(
                    "animate"
                );

            }
        );

        return;

    }


    const observer =
        new IntersectionObserver(
            function (entries) {

                entries.forEach(
                    function (entry) {

                        if (
                            entry.isIntersecting
                        ) {

                            entry.target.classList.add(
                                "animate"
                            );


                            observer.unobserve(
                                entry.target
                            );

                        }

                    }
                );

            },
            {
                threshold: 0.12
            }
        );


    elements.forEach(
        function (element) {

            observer.observe(
                element
            );

        }
    );

}


// =========================================================
// DARK MODE
// =========================================================

function initializeTheme() {

    const savedTheme =
        localStorage.getItem(
            "theme"
        );


    if (
        savedTheme === "dark"
    ) {

        document.body.classList.add(
            "dark"
        );

    }


    updateThemeButton();

}


// =========================================================
// TOGGLE DARK MODE
// =========================================================

function toggleDarkMode() {

    document.body.classList.toggle(
        "dark"
    );


    const theme =
        document.body.classList.contains(
            "dark"
        )
            ? "dark"
            : "light";


    try {

        localStorage.setItem(
            "theme",
            theme
        );

    }

    catch (error) {

        console.warn(
            "Unable to save theme.",
            error
        );

    }


    updateThemeButton();

}


// =========================================================
// UPDATE THEME BUTTON
// =========================================================

function updateThemeButton() {

    const buttons =
        document.querySelectorAll(
            "[data-theme-toggle]"
        );


    const isDark =
        document.body.classList.contains(
            "dark"
        );


    buttons.forEach(
        function (button) {

            button.setAttribute(
                "aria-pressed",
                isDark
                    ? "true"
                    : "false"
            );


            button.textContent =
                isDark
                    ? "☀️"
                    : "🌙";

        }
    );

}


// =========================================================
// SMOOTH SCROLL
// =========================================================

function initializeSmoothScroll() {

    document.querySelectorAll(
        "a[href^='#']"
    ).forEach(
        function (anchor) {

            anchor.addEventListener(
                "click",
                function (event) {

                    const selector =
                        this.getAttribute(
                            "href"
                        );


                    if (
                        !selector ||
                        selector === "#"
                    ) {

                        return;

                    }


                    const target =
                        document.querySelector(
                            selector
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
// DASHBOARD BUTTONS
// =========================================================

function initializeDashboardButtons() {

    const refreshButtons =
        document.querySelectorAll(
            "[data-refresh-dashboard]"
        );


    refreshButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                async function () {

                    button.disabled =
                        true;


                    const oldText =
                        button.textContent;


                    button.textContent =
                        "↻ Refreshing...";


                    try {

                        await refreshWeather();

                        showNotification(
                            "Dashboard data refreshed.",
                            "success"
                        );

                    }

                    catch (error) {

                        showNotification(
                            "Unable to refresh dashboard.",
                            "error"
                        );

                    }

                    finally {

                        button.disabled =
                            false;

                        button.textContent =
                            oldText;

                    }

                }
            );

        }
    );

}


// =========================================================
// MOBILE RESPONSIVE HELPER
// =========================================================

window.addEventListener(
    "resize",
    function () {

        if (
            window.innerWidth <= 768
        ) {

            document
                .querySelectorAll(
                    ".dashboard-hover"
                )
                .forEach(
                    function (element) {

                        element.classList.remove(
                            "dashboard-hover"
                        );

                    }
                );

        }

    }
);


// =========================================================
// PAGE VISIBILITY
// =========================================================

document.addEventListener(
    "visibilitychange",
    function () {

        if (
            !document.hidden
        ) {

            updateClock();

        }

    }
);


// =========================================================
// GLOBAL API
// =========================================================

window.KisanVisionDashboard = {

    refreshWeather:
        refreshWeather,

    showNotification:
        showNotification,

    toggleDarkMode:
        toggleDarkMode,

    updateClock:
        updateClock,

    animateNumber:
        animateNumber

};


// =========================================================
// END
// =========================================================

console.log(
    "🚜 KisanVision360+ Dashboard JS ready."
);