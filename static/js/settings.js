// =========================================================
// KISANVISION360+ SETTINGS JAVASCRIPT
// Global Language • Google Translate • Theme • Notifications
// =========================================================

"use strict";


// =========================================================
// CONFIGURATION
// =========================================================

const SETTINGS_CONFIG = {
    languageEndpoint: "/set-language",
    notificationEndpoint: "/notification",
    weatherEndpoint: "/weather/live",

    languageStorageKey: "kisanvision360_language",
    themeStorageKey: "kisanvision360_theme",
    notificationStorageKey: "kisanvision360_notification"
};


// =========================================================
// SUPPORTED LANGUAGES
// =========================================================

const SUPPORTED_LANGUAGES = {
    en: "English",
    hi: "Hindi",
    mr: "Marathi",
    kn: "Kannada",
    te: "Telugu",
    ta: "Tamil",
    ml: "Malayalam",
    gu: "Gujarati",
    pa: "Punjabi",
    bn: "Bengali",
    as: "Assamese",
    or: "Odia",
    ur: "Urdu",
    ne: "Nepali",
    sa: "Sanskrit",
    kok: "Konkani",
    mai: "Maithili",
    ks: "Kashmiri",
    sd: "Sindhi",
    mni: "Manipuri"
};


// =========================================================
// RTL LANGUAGES
// =========================================================

const RTL_LANGUAGES = [
    "ur",
    "ks",
    "sd"
];


// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    loadTheme();
    loadLanguage();
    loadNotification();

    setupSearch();
    setupSettingsCards();

    updateClock();

    setInterval(updateClock, 1000);

    initializeWeather();

    // Wait for Google Translate
    setTimeout(function () {
        applySavedGoogleLanguage();
    }, 1000);

    console.log("⚙️ KisanVision360+ Settings loaded.");

});


// =========================================================
// THEME
// =========================================================

function toggleTheme() {

    const body = document.body;

    if (!body) {
        return;
    }

    body.classList.toggle("dark");

    const isDark =
        body.classList.contains("dark");

    const theme =
        isDark ? "dark" : "light";

    localStorage.setItem(
        SETTINGS_CONFIG.themeStorageKey,
        theme
    );

    localStorage.setItem(
        "theme",
        theme
    );

    updateThemeControls(isDark);

    showSettingsMessage(
        isDark
            ? "Dark mode enabled."
            : "Light mode enabled.",
        "success"
    );
}


// =========================================================
// LOAD THEME
// =========================================================

function loadTheme() {

    const savedTheme =
        localStorage.getItem(
            SETTINGS_CONFIG.themeStorageKey
        );

    const oldTheme =
        localStorage.getItem("theme");

    const theme =
        savedTheme ||
        oldTheme ||
        "light";

    if (theme === "dark") {

        document.body.classList.add("dark");

    } else {

        document.body.classList.remove("dark");

    }

    updateThemeControls(
        theme === "dark"
    );
}


// =========================================================
// UPDATE THEME CONTROLS
// =========================================================

function updateThemeControls(isDark) {

    const toggle =
        document.getElementById("themeToggle");

    if (toggle) {
        toggle.checked = isDark;
    }

    const label =
        document.getElementById("themeStatus");

    if (label) {

        label.textContent =
            isDark
                ? "Dark Mode"
                : "Light Mode";
    }
}


// =========================================================
// LANGUAGE
// =========================================================

async function changeLanguage() {

    const selector =
        document.getElementById("language");

    /*
     * Support both:
     * #language
     * #globalLanguage
     */

    const globalSelector =
        document.getElementById("globalLanguage");

    const languageSelect =
        selector || globalSelector;

    if (!languageSelect) {

        console.error(
            "Language selector not found."
        );

        return;
    }

    const language =
        String(
            languageSelect.value || "en"
        )
            .toLowerCase()
            .trim();

    await setApplicationLanguage(language);
}


// =========================================================
// GLOBAL LANGUAGE
// =========================================================

async function applyGlobalLanguage() {

    const selector =
        document.getElementById(
            "globalLanguage"
        );

    if (!selector) {

        console.error(
            "#globalLanguage not found."
        );

        return;
    }

    const language =
        String(
            selector.value || "en"
        )
            .toLowerCase()
            .trim();

    await setApplicationLanguage(language);
}


// =========================================================
// SET APPLICATION LANGUAGE
// =========================================================

async function setApplicationLanguage(language) {

    if (
        !Object.prototype.hasOwnProperty.call(
            SUPPORTED_LANGUAGES,
            language
        )
    ) {

        showSettingsMessage(
            "Unsupported language selected.",
            "error"
        );

        return false;
    }

    const languageName =
        SUPPORTED_LANGUAGES[language];

    console.log(
        "🌐 Selected language:",
        language,
        languageName
    );


    // =====================================================
    // SAVE LOCAL STORAGE
    // =====================================================

    localStorage.setItem(
        SETTINGS_CONFIG.languageStorageKey,
        language
    );

    localStorage.setItem(
        "language",
        language
    );


    // =====================================================
    // UPDATE HTML LANGUAGE
    // =====================================================

    document.documentElement.lang =
        language;

    document.documentElement.dir =
        RTL_LANGUAGES.includes(language)
            ? "rtl"
            : "ltr";


    // =====================================================
    // UPDATE SELECTORS
    // =====================================================

    const languageSelector =
        document.getElementById("language");

    const globalSelector =
        document.getElementById("globalLanguage");

    if (languageSelector) {
        languageSelector.value = language;
    }

    if (globalSelector) {
        globalSelector.value = language;
    }


    // =====================================================
    // STATUS
    // =====================================================

    updateLanguageStatus(
        language,
        languageName
    );


    // =====================================================
    // SAVE FLASK SESSION + DATABASE
    // =====================================================

    try {

        const response =
            await fetch(
                SETTINGS_CONFIG.languageEndpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body:
                        JSON.stringify({
                            language: language
                        })
                }
            );


        let data = {};

        try {

            data =
                await response.json();

        } catch (jsonError) {

            console.warn(
                "Server response was not JSON.",
                jsonError
            );

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                `HTTP ${response.status}`
            );
        }


        if (
            data &&
            data.success === false
        ) {

            throw new Error(
                data.message ||
                "Language update failed."
            );
        }


        // =================================================
        // RTL FROM SERVER
        // =================================================

        if (
            data &&
            data.direction
        ) {

            document.documentElement.dir =
                data.direction;
        }


        // =================================================
        // GOOGLE TRANSLATE
        // =================================================

        if (language === "en") {

            clearGoogleTranslation();

        } else {

            const ready =
                await waitForGoogleTranslate();

            if (ready) {

                applyGoogleTranslate(
                    language
                );

            } else {

                console.warn(
                    "Google Translate did not load."
                );

            }
        }


        showSettingsMessage(
            `Language changed to ${languageName}.`,
            "success"
        );

        console.log(
            "✅ Language successfully changed:",
            language
        );

        /*
         * Reload after a short delay.
         *
         * This makes the Flask session language
         * active throughout the application.
         */

        setTimeout(function () {

            window.location.reload();

        }, 1000);

        return true;

    }

    catch (error) {

        console.error(
            "❌ Language update error:",
            error
        );

        /*
         * Local language is already saved,
         * but backend synchronization failed.
         */

        showSettingsMessage(
            "Language applied locally, but server synchronization failed.",
            "warning"
        );

        return false;
    }
}


// =========================================================
// LOAD LANGUAGE
// =========================================================

function loadLanguage() {

    const languageSelector =
        document.getElementById("language");

    const globalSelector =
        document.getElementById("globalLanguage");

    const savedLanguage =
        localStorage.getItem(
            SETTINGS_CONFIG.languageStorageKey
        ) ||
        localStorage.getItem("language") ||
        document.documentElement.lang ||
        "en";

    const language =
        Object.prototype.hasOwnProperty.call(
            SUPPORTED_LANGUAGES,
            savedLanguage
        )
            ? savedLanguage
            : "en";


    if (languageSelector) {

        languageSelector.value =
            language;

    }


    if (globalSelector) {

        globalSelector.value =
            language;

    }


    document.documentElement.lang =
        language;

    document.documentElement.dir =
        RTL_LANGUAGES.includes(language)
            ? "rtl"
            : "ltr";


    updateLanguageStatus(
        language,
        SUPPORTED_LANGUAGES[language]
    );
}


// =========================================================
// LANGUAGE STATUS
// =========================================================

function updateLanguageStatus(
    language,
    languageName
) {

    const status =
        document.getElementById(
            "languageStatus"
        );

    if (!status) {
        return;
    }

    status.textContent =
        `Current language: ${languageName} (${language})`;
}


// =========================================================
// GOOGLE TRANSLATE
// =========================================================

function applyGoogleTranslate(language) {

    const googleSelect =
        document.querySelector(
            ".goog-te-combo"
        );

    if (!googleSelect) {

        console.error(
            "Google Translate selector not found."
        );

        return false;
    }


    console.log(
        "🌐 Applying Google Translate:",
        language
    );


    googleSelect.value =
        language;


    googleSelect.dispatchEvent(
        new Event(
            "change",
            {
                bubbles: true
            }
        )
    );


    return true;
}


// =========================================================
// WAIT FOR GOOGLE TRANSLATE
// =========================================================

function waitForGoogleTranslate() {

    return new Promise(function (resolve) {

        let attempts = 0;

        const maxAttempts = 50;

        const timer =
            setInterval(function () {

                const googleSelect =
                    document.querySelector(
                        ".goog-te-combo"
                    );

                if (googleSelect) {

                    clearInterval(timer);

                    console.log(
                        "✅ Google Translate ready."
                    );

                    resolve(true);

                    return;
                }


                attempts++;


                if (
                    attempts >= maxAttempts
                ) {

                    clearInterval(timer);

                    console.warn(
                        "⚠️ Google Translate not loaded."
                    );

                    resolve(false);
                }

            }, 200);

    });
}


// =========================================================
// APPLY SAVED GOOGLE LANGUAGE
// =========================================================

async function applySavedGoogleLanguage() {

    const language =
        localStorage.getItem(
            SETTINGS_CONFIG.languageStorageKey
        ) ||
        localStorage.getItem("language") ||
        "en";


    if (
        !Object.prototype.hasOwnProperty.call(
            SUPPORTED_LANGUAGES,
            language
        )
    ) {

        return;
    }


    document.documentElement.lang =
        language;

    document.documentElement.dir =
        RTL_LANGUAGES.includes(language)
            ? "rtl"
            : "ltr";


    if (language === "en") {

        clearGoogleTranslation();

        return;
    }


    const ready =
        await waitForGoogleTranslate();


    if (ready) {

        applyGoogleTranslate(
            language
        );

    }
}


// =========================================================
// CLEAR GOOGLE TRANSLATION
// =========================================================

function clearGoogleTranslation() {

    const googleSelect =
        document.querySelector(
            ".goog-te-combo"
        );


    if (googleSelect) {

        googleSelect.value = "en";

        googleSelect.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true
                }
            )
        );
    }


    try {

        document.cookie =
            "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

        document.cookie =
            "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" +
            location.hostname +
            ";";

    } catch (error) {

        console.warn(
            "Unable to clear Google Translate cookie.",
            error
        );
    }


    console.log(
        "🌐 Google Translate reset to English."
    );
}


// =========================================================
// NOTIFICATION TOGGLE
// =========================================================

async function toggleNotification() {

    const checkbox =
        document.getElementById("notify");

    if (!checkbox) {
        return;
    }

    const enabled =
        checkbox.checked;


    localStorage.setItem(
        SETTINGS_CONFIG.notificationStorageKey,
        enabled ? "ON" : "OFF"
    );

    localStorage.setItem(
        "notification",
        enabled ? "ON" : "OFF"
    );


    updateNotificationStatus(
        enabled
    );


    // =====================================================
    // BROWSER PERMISSION
    // =====================================================

    if (
        enabled &&
        "Notification" in window
    ) {

        try {

            if (
                Notification.permission ===
                "default"
            ) {

                await Notification.requestPermission();

            }

        } catch (error) {

            console.warn(
                "Notification permission unavailable:",
                error
            );

        }
    }


    // =====================================================
    // BACKEND
    // =====================================================

    try {

        const body =
            new URLSearchParams();

        body.append(
            "status",
            enabled ? "true" : "false"
        );


        const response =
            await fetch(
                SETTINGS_CONFIG.notificationEndpoint,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded",

                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    body:
                        body.toString()
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        showSettingsMessage(
            enabled
                ? "Notifications enabled."
                : "Notifications disabled.",
            "success"
        );

    }

    catch (error) {

        console.error(
            "❌ Notification update error:",
            error
        );

        showSettingsMessage(
            enabled
                ? "Notifications enabled on this device."
                : "Notifications disabled on this device.",
            "warning"
        );
    }
}


// =========================================================
// LOAD NOTIFICATION
// =========================================================

function loadNotification() {

    const checkbox =
        document.getElementById("notify");

    if (!checkbox) {
        return;
    }


    const saved =
        localStorage.getItem(
            SETTINGS_CONFIG.notificationStorageKey
        );

    const oldSaved =
        localStorage.getItem("notification");


    const value =
        saved !== null
            ? saved
            : oldSaved;


    if (value === null) {

        checkbox.checked = true;

    } else {

        checkbox.checked =
            value === "ON" ||
            value === "true";

    }


    updateNotificationStatus(
        checkbox.checked
    );
}


// =========================================================
// NOTIFICATION STATUS
// =========================================================

function updateNotificationStatus(enabled) {

    const status =
        document.getElementById(
            "notificationStatus"
        );

    if (!status) {
        return;
    }


    status.textContent =
        enabled
            ? "Notifications Enabled"
            : "Notifications Disabled";


    status.dataset.status =
        enabled
            ? "enabled"
            : "disabled";
}


// =========================================================
// LOGOUT
// =========================================================

function logoutConfirm() {

    const confirmed =
        window.confirm(
            "Do you really want to logout?"
        );


    if (!confirmed) {
        return;
    }


    document
        .querySelectorAll("[data-logout]")
        .forEach(function (button) {

            button.disabled = true;

        });


    window.location.href =
        "/logout";
}


// =========================================================
// SEARCH
// =========================================================

function setupSearch() {

    const input =
        document.getElementById(
            "searchSettings"
        ) ||
        document.getElementById(
            "search"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "input",
        function () {

            filterSettingsCards(
                this.value
            );

        }
    );
}


// =========================================================
// SEARCH SETTINGS
// =========================================================

function searchSettings() {

    const input =
        document.getElementById("search") ||
        document.getElementById("searchSettings");


    if (!input) {
        return;
    }


    filterSettingsCards(
        input.value
    );
}


// =========================================================
// FILTER SETTINGS CARDS
// =========================================================

function filterSettingsCards(value) {

    const filter =
        String(value || "")
            .toLowerCase()
            .trim();


    const cards =
        document.querySelectorAll(
            ".setting-card, .settings-card, .card"
        );


    let visible = 0;


    cards.forEach(function (card) {

        const text =
            (
                card.innerText ||
                card.textContent ||
                ""
            ).toLowerCase();


        const matches =
            text.includes(filter);


        card.style.display =
            matches ? "" : "none";


        if (matches) {
            visible++;
        }

    });


    const count =
        document.getElementById(
            "settingsSearchCount"
        );


    if (count) {

        count.textContent =
            `${visible} setting${visible === 1 ? "" : "s"} found`;

    }
}


// =========================================================
// SETTINGS CARD SETUP
// =========================================================

function setupSettingsCards() {

    document
        .querySelectorAll(
            ".setting-card, .settings-card"
        )
        .forEach(function (card) {

            card.addEventListener(
                "mouseenter",
                function () {

                    this.classList.add(
                        "settings-card-hover"
                    );

                }
            );


            card.addEventListener(
                "mouseleave",
                function () {

                    this.classList.remove(
                        "settings-card-hover"
                    );

                }
            );

        });
}


// =========================================================
// SHOW MESSAGE
// =========================================================

function showMessage(message) {

    showSettingsMessage(
        message,
        "success"
    );
}


// =========================================================
// SETTINGS TOAST
// =========================================================

function showSettingsMessage(
    message,
    type = "info"
) {

    let toast =
        document.getElementById(
            "settingsToast"
        );


    if (!toast) {

        toast =
            document.createElement("div");

        toast.id =
            "settingsToast";

        toast.className =
            "settings-toast";

        document.body.appendChild(
            toast
        );
    }


    toast.className =
        `settings-toast ${type}`;


    toast.textContent =
        message;


    requestAnimationFrame(function () {

        toast.classList.add("show");

    });


    clearTimeout(
        toast._hideTimer
    );


    toast._hideTimer =
        setTimeout(function () {

            toast.classList.remove(
                "show"
            );

        }, 3500);
}


// =========================================================
// CLOCK
// =========================================================

function updateClock() {

    const clock =
        document.getElementById("clock");

    if (!clock) {
        return;
    }


    const now =
        new Date();


    try {

        clock.textContent =
            now.toLocaleTimeString(
                "en-IN",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            );

    } catch (error) {

        clock.textContent =
            now.toLocaleTimeString();

    }
}


// =========================================================
// WEATHER
// =========================================================

async function refreshWeather() {

    try {

        const response =
            await fetch(
                SETTINGS_CONFIG.weatherEndpoint,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    },

                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        updateWeatherUI(
            data
        );


        return data;

    } catch (error) {

        console.error(
            "❌ Weather refresh error:",
            error
        );

        showSettingsMessage(
            "Unable to refresh live weather.",
            "warning"
        );

        return null;
    }
}


// =========================================================
// INITIALIZE WEATHER
// =========================================================

function initializeWeather() {

    const weatherElements =
        document.querySelectorAll(
            "#temp, [data-weather-temperature]"
        );


    if (
        weatherElements.length === 0
    ) {

        return;
    }


    setInterval(
        refreshWeather,
        600000
    );
}


// =========================================================
// UPDATE WEATHER UI
// =========================================================

function updateWeatherUI(data) {

    if (!data) {
        return;
    }


    const temperature =
        data.temperature ??
        data.temp;


    if (
        temperature !== undefined &&
        temperature !== null
    ) {

        const temp =
            document.getElementById("temp");


        if (temp) {

            temp.textContent =
                `${temperature}°C`;

        }


        document
            .querySelectorAll(
                "[data-weather-temperature]"
            )
            .forEach(function (element) {

                element.textContent =
                    `${temperature}°C`;

            });
    }


    const humidity =
        data.humidity;


    if (
        humidity !== undefined &&
        humidity !== null
    ) {

        document
            .querySelectorAll(
                "[data-weather-humidity]"
            )
            .forEach(function (element) {

                element.textContent =
                    `${humidity}%`;

            });
    }


    const description =
        data.description ||
        data.condition;


    if (description) {

        document
            .querySelectorAll(
                "[data-weather-description]"
            )
            .forEach(function (element) {

                element.textContent =
                    description;

            });
    }
}


// =========================================================
// GLOBAL API
// =========================================================

window.KisanVisionSettings = {

    toggleTheme:
        toggleTheme,

    changeLanguage:
        changeLanguage,

    applyGlobalLanguage:
        applyGlobalLanguage,

    setApplicationLanguage:
        setApplicationLanguage,

    toggleNotification:
        toggleNotification,

    logoutConfirm:
        logoutConfirm,

    searchSettings:
        searchSettings,

    refreshWeather:
        refreshWeather,

    showMessage:
        showMessage,

    applyGoogleLanguage:
        applyGoogleTranslate,

    clearGoogleTranslation:
        clearGoogleTranslation
};


// =========================================================
// GLOBAL FUNCTIONS
// =========================================================

window.changeLanguage =
    changeLanguage;

window.applyGlobalLanguage =
    applyGlobalLanguage;

window.toggleTheme =
    toggleTheme;

window.toggleNotification =
    toggleNotification;

window.logoutConfirm =
    logoutConfirm;


// =========================================================
// END
// =========================================================

console.log(
    "⚙️ KisanVision360+ Settings JS ready."
);