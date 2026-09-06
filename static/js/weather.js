/* =========================================================
   KISANVISION360+ WEATHER JAVASCRIPT
   File: static/js/weather.js
========================================================= */

"use strict";

document.addEventListener("DOMContentLoaded", () => {

    const CONFIG = {
        refreshInterval: 10 * 60 * 1000,

        weatherEndpoint: "/api/weather",
        forecastEndpoint: "/api/weather/forecast",
        intelligenceEndpoint: "/api/weather/intelligence",

        language:
            document.documentElement.lang ||
            localStorage.getItem("kisanvision360_language") ||
            "en"
    };

    /* =====================================================
       DOM HELPERS
    ===================================================== */

    const $ = (id) => document.getElementById(id);

    const setText = (id, value, fallback = "N/A") => {
        const element = $(id);

        if (!element) return;

        if (
            value === undefined ||
            value === null ||
            value === ""
        ) {
            element.textContent = fallback;
        } else {
            element.textContent = value;
        }
    };

    const safeNumber = (value, decimals = 1) => {
        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "N/A";
        }

        return number.toFixed(decimals);
    };

    /* =====================================================
       GLOBAL STATE
    ===================================================== */

    let currentWeather = null;
    let currentForecast = [];
    let currentIntelligence = null;

    let refreshTimer = null;
    let isLoading = false;

    /* =====================================================
       LOADING
    ===================================================== */

    function showLoading() {
        isLoading = true;

        document.body.classList.add("weather-loading");

        const loader = $("weatherLoader");

        if (loader) {
            loader.style.display = "flex";
        }
    }

    function hideLoading() {
        isLoading = false;

        document.body.classList.remove("weather-loading");

        const loader = $("weatherLoader");

        if (loader) {
            loader.style.display = "none";
        }
    }

    /* =====================================================
       ERROR MESSAGE
    ===================================================== */

    function showError(message) {

        const errorBox =
            $("weatherError") ||
            $("weather-error");

        if (!errorBox) {
            console.error(message);
            return;
        }

        errorBox.textContent = message;
        errorBox.style.display = "block";

        setTimeout(() => {
            errorBox.style.display = "none";
        }, 6000);
    }

    /* =====================================================
       API HELPER
    ===================================================== */

    async function apiRequest(url) {

        const response = await fetch(url, {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            cache: "no-store"
        });

        let data = {};

        try {
            data = await response.json();
        } catch (error) {
            throw new Error("Invalid server response.");
        }

        if (response.status === 401) {
            throw new Error("Please login to view weather information.");
        }

        if (!response.ok || data.success === false) {
            throw new Error(
                data.message ||
                data.error ||
                "Unable to load weather data."
            );
        }

        return data;
    }

    /* =====================================================
       WEATHER ICON
    ===================================================== */

    function getWeatherIcon(data) {

        if (!data) {
            return "☀️";
        }

        const icon =
            data.icon ||
            data.weather_icon ||
            data.icon_code ||
            "";

        const description =
            String(
                data.description ||
                data.weather ||
                ""
            ).toLowerCase();

        if (icon) {

            const iconMap = {
                "01d": "☀️",
                "01n": "🌙",
                "02d": "🌤️",
                "02n": "☁️",
                "03d": "☁️",
                "03n": "☁️",
                "04d": "☁️",
                "04n": "☁️",
                "09d": "🌧️",
                "09n": "🌧️",
                "10d": "🌦️",
                "10n": "🌧️",
                "11d": "⛈️",
                "11n": "⛈️",
                "13d": "❄️",
                "13n": "❄️",
                "50d": "🌫️",
                "50n": "🌫️"
            };

            if (iconMap[icon]) {
                return iconMap[icon];
            }
        }

        if (description.includes("thunder")) {
            return "⛈️";
        }

        if (description.includes("rain")) {
            return "🌧️";
        }

        if (description.includes("cloud")) {
            return "☁️";
        }

        if (
            description.includes("mist") ||
            description.includes("fog")
        ) {
            return "🌫️";
        }

        if (description.includes("clear")) {
            return "☀️";
        }

        return "🌤️";
    }

    /* =====================================================
       UPDATE CURRENT WEATHER
    ===================================================== */

    function updateWeatherUI(data) {

        if (!data) return;

        currentWeather = data;

        /*
         * Backend may return:
         *
         * {
         *   temperature,
         *   feels_like,
         *   humidity,
         *   wind_speed,
         *   pressure,
         *   rainfall,
         *   clouds,
         *   visibility,
         *   description,
         *   city,
         *   icon,
         *   ...
         * }
         */

        const temperature =
            data.temperature ??
            data.temp ??
            data.temperature_c;

        const feelsLike =
            data.feels_like ??
            data.feelsLike;

        const humidity =
            data.humidity;

        const windSpeed =
            data.wind_speed ??
            data.windSpeed;

        const pressure =
            data.pressure;

        const rainfall =
            data.rainfall ??
            data.rain ??
            data.rainfall_mm;

        const clouds =
            data.clouds ??
            data.cloudiness;

        const visibility =
            data.visibility;

        const description =
            data.description ??
            data.weather ??
            data.condition;

        const city =
            data.city ??
            data.location ??
            "Nagpur";

        /* ===============================================
           MAIN WEATHER VALUES
        =============================================== */

        setText(
            "temperature",
            Number.isFinite(Number(temperature))
                ? `${safeNumber(temperature)}°C`
                : "N/A"
        );

        setText(
            "temp",
            Number.isFinite(Number(temperature))
                ? `${safeNumber(temperature)}°C`
                : "N/A"
        );

        setText(
            "feelsLike",
            Number.isFinite(Number(feelsLike))
                ? `${safeNumber(feelsLike)}°C`
                : "N/A"
        );

        setText(
            "humidity",
            Number.isFinite(Number(humidity))
                ? `${safeNumber(humidity, 0)}%`
                : "N/A"
        );

        setText(
            "wind",
            Number.isFinite(Number(windSpeed))
                ? `${safeNumber(windSpeed)} m/s`
                : "N/A"
        );

        setText(
            "windSpeed",
            Number.isFinite(Number(windSpeed))
                ? `${safeNumber(windSpeed)} m/s`
                : "N/A"
        );

        setText(
            "pressure",
            Number.isFinite(Number(pressure))
                ? `${safeNumber(pressure, 0)} hPa`
                : "N/A"
        );

        setText(
            "rainfall",
            Number.isFinite(Number(rainfall))
                ? `${safeNumber(rainfall)} mm`
                : "0 mm"
        );

        setText(
            "clouds",
            Number.isFinite(Number(clouds))
                ? `${safeNumber(clouds, 0)}%`
                : "N/A"
        );

        setText(
            "visibility",
            Number.isFinite(Number(visibility))
                ? `${safeNumber(visibility, 1)} km`
                : "N/A"
        );

        setText(
            "description",
            description || "Weather information unavailable"
        );

        setText(
            "city",
            city,
            "Nagpur"
        );

        setText(
            "location",
            city,
            "Nagpur"
        );

        setText(
            "weatherCity",
            city,
            "Nagpur"
        );

        /* ===============================================
           WEATHER ICON
        =============================================== */

        const iconElement =
            $("weatherIcon") ||
            $("weather-icon");

        if (iconElement) {
            iconElement.textContent = getWeatherIcon(data);
        }

        /* ===============================================
           UPDATED TIME
        =============================================== */

        if (data.updated_at) {

            setText(
                "updatedAt",
                `Updated: ${formatDateTime(data.updated_at)}`
            );
        }

        /* ===============================================
           WEATHER THEME
        =============================================== */

        applyWeatherTheme(data);

        /* ===============================================
           INSIGHTS
        =============================================== */

        calculateWeatherInsights(data);
    }

    /* =====================================================
       DATE/TIME FORMAT
    ===================================================== */

    function formatDateTime(value) {

        if (!value) {
            return "N/A";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return date.toLocaleString(
            undefined,
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            }
        );
    }

    /* =====================================================
       WEATHER THEME
    ===================================================== */

    function applyWeatherTheme(data) {

        const body = document.body;

        if (!body || !data) return;

        body.classList.remove(
            "weather-clear",
            "weather-cloudy",
            "weather-rain",
            "weather-storm"
        );

        const description =
            String(
                data.description ||
                data.weather ||
                ""
            ).toLowerCase();

        if (
            description.includes("thunder") ||
            description.includes("storm")
        ) {

            body.classList.add("weather-storm");

        } else if (
            description.includes("rain") ||
            description.includes("drizzle")
        ) {

            body.classList.add("weather-rain");

        } else if (
            description.includes("cloud")
        ) {

            body.classList.add("weather-cloudy");

        } else {

            body.classList.add("weather-clear");
        }
    }

    /* =====================================================
       WEATHER INSIGHTS
    ===================================================== */

    function calculateWeatherInsights(data) {

        if (!data) return;

        const humidity = Number(data.humidity || 0);

        const rainfall = Number(
            data.rainfall ??
            data.rain ??
            0
        );

        const wind = Number(
            data.wind_speed ??
            data.windSpeed ??
            0
        );

        const temperature = Number(
            data.temperature ??
            data.temp ??
            0
        );

        let rainRisk = "Low";
        let humidityRisk = "Low";
        let windRisk = "Low";

        /* ===============================================
           RAIN RISK
        =============================================== */

        if (rainfall >= 20) {
            rainRisk = "High";
        } else if (rainfall >= 5) {
            rainRisk = "Medium";
        }

        /* ===============================================
           HUMIDITY RISK
        =============================================== */

        if (humidity >= 80) {
            humidityRisk = "High";
        } else if (humidity >= 65) {
            humidityRisk = "Medium";
        }

        /* ===============================================
           WIND RISK
        =============================================== */

        if (wind >= 10) {
            windRisk = "High";
        } else if (wind >= 6) {
            windRisk = "Medium";
        }

        setText("rainRisk", rainRisk);
        setText("humidityRisk", humidityRisk);
        setText("windRisk", windRisk);

        /* ===============================================
           IRRIGATION INSIGHT
        =============================================== */

        let irrigationMessage =
            "Check soil moisture before irrigation.";

        if (rainfall >= 5) {

            irrigationMessage =
                "Recent rainfall may reduce the need for irrigation.";

        } else if (temperature >= 35 && humidity < 50) {

            irrigationMessage =
                "Hot and dry conditions detected. Check soil moisture frequently.";

        } else if (humidity >= 80) {

            irrigationMessage =
                "High humidity detected. Avoid unnecessary irrigation.";

        }

        setText(
            "irrigationInsight",
            irrigationMessage
        );

        /* ===============================================
           CROP INSIGHT
        =============================================== */

        let cropMessage =
            "Weather conditions should be monitored for crop planning.";

        if (rainfall >= 5) {

            cropMessage =
                "Rainfall is available. Review crop drainage and field conditions.";

        } else if (
            temperature >= 30 &&
            humidity >= 60
        ) {

            cropMessage =
                "Warm and humid conditions may support crop growth but increase disease pressure.";

        } else if (temperature < 15) {

            cropMessage =
                "Cool conditions detected. Monitor temperature-sensitive crops.";

        }

        setText(
            "cropInsight",
            cropMessage
        );

        /* ===============================================
           DISEASE INSIGHT
        =============================================== */

        let diseaseMessage =
            "Continue regular crop monitoring.";

        if (humidity >= 80) {

            diseaseMessage =
                "High humidity can increase disease pressure. Monitor crops regularly.";

        } else if (humidity >= 65 && rainfall > 0) {

            diseaseMessage =
                "Moist conditions detected. Check leaves for early disease symptoms.";

        }

        setText(
            "diseaseInsight",
            diseaseMessage
        );

        /* ===============================================
           FIELD INSIGHT
        =============================================== */

        let fieldMessage =
            "Field conditions look suitable for routine monitoring.";

        if (wind >= 10) {

            fieldMessage =
                "Strong winds detected. Protect young plants and inspect structures.";

        } else if (rainfall >= 20) {

            fieldMessage =
                "Heavy rainfall detected. Check field drainage and waterlogging.";

        }

        setText(
            "fieldInsight",
            fieldMessage
        );

        /* ===============================================
           SMART ADVICE
        =============================================== */

        updateSmartAdvice(data);
    }

    /* =====================================================
       SMART ADVICE
    ===================================================== */

    function updateSmartAdvice(data) {

        const adviceList = [];

        if (Array.isArray(data.advice)) {
            adviceList.push(...data.advice);
        }

        const humidity = Number(data.humidity || 0);

        const rainfall = Number(
            data.rainfall ??
            data.rain ??
            0
        );

        const temperature = Number(
            data.temperature ??
            data.temp ??
            0
        );

        if (
            temperature >= 35 &&
            humidity < 50
        ) {
            adviceList.push(
                "High temperature with low humidity detected. Monitor crop water stress."
            );
        }

        if (rainfall >= 20) {
            adviceList.push(
                "Heavy rainfall detected. Check drainage and avoid unnecessary irrigation."
            );
        }

        if (humidity >= 80) {
            adviceList.push(
                "High humidity detected. Monitor crops for fungal disease symptoms."
            );
        }

        if (adviceList.length === 0) {
            adviceList.push(
                "Continue monitoring weather and soil conditions before farm operations."
            );
        }

        const title =
            $("smartAdviceTitle");

        if (title) {
            title.textContent =
                "AI Weather-Based Farm Advice";
        }

        const container =
            $("smartAdvice");

        if (!container) return;

        container.innerHTML = "";

        adviceList
            .slice(0, 6)
            .forEach((advice) => {

                const item =
                    document.createElement("div");

                item.className =
                    "smart-advice-item";

                item.innerHTML = `
                    <span class="advice-icon">🌱</span>
                    <span>${escapeHTML(advice)}</span>
                `;

                container.appendChild(item);
            });
    }

    /* =====================================================
       LOAD FORECAST
    ===================================================== */

    async function loadForecast() {

        try {

            const data =
                await apiRequest(
                    CONFIG.forecastEndpoint
                );

            currentForecast =
                data.forecast ||
                data.data ||
                [];

            renderForecast(currentForecast);

        } catch (error) {

            console.warn(
                "Forecast loading failed:",
                error.message
            );
        }
    }

    /* =====================================================
       RENDER FORECAST
    ===================================================== */

    function renderForecast(forecast) {

        const grid =
            $("forecastGrid");

        if (!grid) return;

        grid.innerHTML = "";

        if (
            !Array.isArray(forecast) ||
            forecast.length === 0
        ) {

            grid.innerHTML = `
                <div class="forecast-empty">
                    Forecast information is currently unavailable.
                </div>
            `;

            return;
        }

        forecast.forEach((item) => {

            const date =
                item.date ||
                item.forecast_date ||
                item.day ||
                "";

            const temp =
                item.temperature ??
                item.temp ??
                item.temp_day;

            const minTemp =
                item.min_temperature ??
                item.temp_min ??
                item.min_temp;

            const maxTemp =
                item.max_temperature ??
                item.temp_max ??
                item.max_temp;

            const humidity =
                item.humidity;

            const rainfall =
                item.rainfall ??
                item.rain ??
                item.rainfall_mm;

            const description =
                item.description ||
                item.weather ||
                "Weather";

            const card =
                document.createElement("div");

            card.className =
                "forecast-card";

            card.innerHTML = `
                <div class="forecast-date">
                    ${escapeHTML(formatForecastDate(date))}
                </div>

                <div class="forecast-icon">
                    ${getWeatherIcon(item)}
                </div>

                <div class="forecast-condition">
                    ${escapeHTML(description)}
                </div>

                <div class="forecast-temp">
                    ${
                        Number.isFinite(Number(temp))
                            ? `${safeNumber(temp)}°C`
                            : "N/A"
                    }
                </div>

                <div class="forecast-details">

                    <span>
                        🌡️
                        ${
                            Number.isFinite(Number(minTemp))
                                ? `${safeNumber(minTemp)}°`
                                : "N/A"
                        }
                        -
                        ${
                            Number.isFinite(Number(maxTemp))
                                ? `${safeNumber(maxTemp)}°`
                                : "N/A"
                        }
                    </span>

                    <span>
                        💧
                        ${
                            Number.isFinite(Number(humidity))
                                ? `${safeNumber(humidity, 0)}%`
                                : "N/A"
                        }
                    </span>

                    <span>
                        🌧️
                        ${
                            Number.isFinite(Number(rainfall))
                                ? `${safeNumber(rainfall)} mm`
                                : "0 mm"
                        }
                    </span>

                </div>
            `;

            grid.appendChild(card);
        });
    }

    /* =====================================================
       FORECAST DATE
    ===================================================== */

    function formatForecastDate(value) {

        if (!value) {
            return "Forecast";
        }

        const date =
            new Date(value);

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return String(value);
        }

        return date.toLocaleDateString(
            undefined,
            {
                weekday: "short",
                day: "numeric",
                month: "short"
            }
        );
    }

    /* =====================================================
       WEATHER INTELLIGENCE API
    ===================================================== */

    async function loadIntelligence() {

        try {

            const data =
                await apiRequest(
                    CONFIG.intelligenceEndpoint
                );

            currentIntelligence =
                data.intelligence ||
                data.data ||
                data;

            applyIntelligence(
                currentIntelligence
            );

        } catch (error) {

            console.warn(
                "Weather intelligence loading failed:",
                error.message
            );
        }
    }

    /* =====================================================
       APPLY INTELLIGENCE
    ===================================================== */

    function applyIntelligence(data) {

        if (!data) return;

        if (data.irrigation) {

            setText(
                "irrigationInsight",
                data.irrigation
            );
        }

        if (data.crop) {

            setText(
                "cropInsight",
                data.crop
            );
        }

        if (data.disease) {

            setText(
                "diseaseInsight",
                data.disease
            );
        }

        if (data.field) {

            setText(
                "fieldInsight",
                data.field
            );
        }

        if (data.rain_risk) {

            setText(
                "rainRisk",
                data.rain_risk
            );
        }

        if (data.humidity_risk) {

            setText(
                "humidityRisk",
                data.humidity_risk
            );
        }

        if (data.wind_risk) {

            setText(
                "windRisk",
                data.wind_risk
            );
        }

        if (
            Array.isArray(data.advice)
        ) {

            updateSmartAdvice({
                advice: data.advice
            });
        }
    }

    /* =====================================================
       LOAD ALL WEATHER DATA
    ===================================================== */

    async function loadWeather(
        showLoader = true
    ) {

        if (isLoading) {
            return;
        }

        try {

            if (showLoader) {
                showLoading();
            }

            const data =
                await apiRequest(
                    CONFIG.weatherEndpoint
                );

            updateWeatherUI(
                data.weather ||
                data.data ||
                data
            );

            await Promise.allSettled([
                loadForecast(),
                loadIntelligence()
            ]);

            updateLastRefresh();

        } catch (error) {

            console.error(
                "Weather error:",
                error
            );

            showError(
                error.message ||
                "Unable to load weather."
            );

        } finally {

            hideLoading();
        }
    }

    /* =====================================================
       LAST REFRESH
    ===================================================== */

    function updateLastRefresh() {

        const element =
            $("lastRefresh");

        if (!element) return;

        element.textContent =
            `Last refreshed: ${
                new Date().toLocaleTimeString(
                    undefined,
                    {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit"
                    }
                )
            }`;
    }

    /* =====================================================
       MANUAL REFRESH
    ===================================================== */

    function refreshWeather() {

        loadWeather(true);
    }

    /* =====================================================
       REFRESH BUTTON
    ===================================================== */

    function setupRefreshButton() {

        const buttons = [
            $("refreshWeather"),
            $("refresh-weather"),
            $("weatherRefresh"),
            $("refreshBtn")
        ];

        buttons.forEach((button) => {

            if (!button) return;

            button.addEventListener(
                "click",
                () => {

                    button.classList.add(
                        "refreshing"
                    );

                    refreshWeather();

                    setTimeout(() => {

                        button.classList.remove(
                            "refreshing"
                        );

                    }, 1000);
                }
            );
        });
    }

    /* =====================================================
       SEARCH CITY
    ===================================================== */

    function setupCitySearch() {

        const input =
            $("citySearch") ||
            $("weatherSearch");

        const button =
            $("citySearchButton") ||
            $("weatherSearchButton");

        if (!input) return;

        async function searchCity() {

            const city =
                input.value.trim();

            if (!city) return;

            /*
             * Current weather endpoint supports:
             * /api/weather?city=Nagpur
             */

            try {

                showLoading();

                const data =
                    await apiRequest(
                        `${CONFIG.weatherEndpoint}?city=${encodeURIComponent(city)}`
                    );

                updateWeatherUI(
                    data.weather ||
                    data.data ||
                    data
                );

                await Promise.allSettled([
                    loadForecastWithCity(city),
                    loadIntelligenceWithCity(city)
                ]);

                updateLastRefresh();

            } catch (error) {

                showError(
                    error.message ||
                    "Unable to find city."
                );

            } finally {

                hideLoading();
            }
        }

        if (button) {

            button.addEventListener(
                "click",
                searchCity
            );
        }

        input.addEventListener(
            "keydown",
            (event) => {

                if (event.key === "Enter") {
                    searchCity();
                }
            }
        );
    }

    /* =====================================================
       CITY FORECAST
    ===================================================== */

    async function loadForecastWithCity(city) {

        try {

            const data =
                await apiRequest(
                    `${CONFIG.forecastEndpoint}?city=${encodeURIComponent(city)}`
                );

            currentForecast =
                data.forecast ||
                data.data ||
                [];

            renderForecast(
                currentForecast
            );

        } catch (error) {

            console.warn(
                error.message
            );
        }
    }

    /* =====================================================
       CITY INTELLIGENCE
    ===================================================== */

    async function loadIntelligenceWithCity(city) {

        try {

            const data =
                await apiRequest(
                    `${CONFIG.intelligenceEndpoint}?city=${encodeURIComponent(city)}`
                );

            currentIntelligence =
                data.intelligence ||
                data.data ||
                data;

            applyIntelligence(
                currentIntelligence
            );

        } catch (error) {

            console.warn(
                error.message
            );
        }
    }

    /* =====================================================
       LIVE CLOCK
    ===================================================== */

    function updateClock() {

        const clock =
            $("liveClock") ||
            $("currentTime");

        if (!clock) return;

        clock.textContent =
            new Date().toLocaleTimeString(
                undefined,
                {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit"
                }
            );
    }

    function startClock() {

        updateClock();

        setInterval(
            updateClock,
            1000
        );
    }

    /* =====================================================
       GREETING
    ===================================================== */

    function updateGreeting() {

        const greeting =
            $("weatherGreeting") ||
            $("greeting");

        if (!greeting) return;

        const hour =
            new Date().getHours();

        let text = "Good morning";

        if (hour >= 12 && hour < 17) {
            text = "Good afternoon";
        } else if (hour >= 17) {
            text = "Good evening";
        }

        const name =
            document.body.dataset.userName ||
            window.KISANVISION_USER_NAME ||
            "";

        greeting.textContent =
            name
                ? `${text}, ${name}!`
                : `${text}!`;
    }

    /* =====================================================
       AUTO REFRESH
    ===================================================== */

    function startAutoRefresh() {

        stopAutoRefresh();

        refreshTimer =
            setInterval(
                () => {

                    if (
                        document.visibilityState ===
                        "visible"
                    ) {
                        loadWeather(false);
                    }

                },
                CONFIG.refreshInterval
            );
    }

    function stopAutoRefresh() {

        if (refreshTimer) {

            clearInterval(
                refreshTimer
            );

            refreshTimer = null;
        }
    }

    /* =====================================================
       VISIBILITY
    ===================================================== */

    document.addEventListener(
        "visibilitychange",
        () => {

            if (
                document.visibilityState ===
                "visible"
            ) {

                loadWeather(false);
            }
        }
    );

    /* =====================================================
       NOTIFICATION BUTTON
    ===================================================== */

    function setupNotificationButton() {

        const button =
            $("notificationButton") ||
            $("notificationBtn");

        if (!button) return;

        button.addEventListener(
            "click",
            () => {

                const notificationSection =
                    $("notifications") ||
                    $("notificationSection");

                if (notificationSection) {

                    notificationSection.scrollIntoView({
                        behavior: "smooth"
                    });
                }
            }
        );
    }

    /* =====================================================
       FORECAST CARD INTERACTION
    ===================================================== */

    function setupForecastInteraction() {

        const grid =
            $("forecastGrid");

        if (!grid) return;

        grid.addEventListener(
            "click",
            (event) => {

                const card =
                    event.target.closest(
                        ".forecast-card"
                    );

                if (!card) return;

                document
                    .querySelectorAll(
                        ".forecast-card.active"
                    )
                    .forEach(
                        (item) =>
                            item.classList.remove(
                                "active"
                            )
                    );

                card.classList.add(
                    "active"
                );
            }
        );
    }

    /* =====================================================
       SMOOTH SCROLL
    ===================================================== */

    function setupSmoothScroll() {

        document
            .querySelectorAll(
                'a[href^="#"]'
            )
            .forEach((link) => {

                link.addEventListener(
                    "click",
                    (event) => {

                        const id =
                            link.getAttribute(
                                "href"
                            );

                        if (
                            !id ||
                            id === "#"
                        ) {
                            return;
                        }

                        const target =
                            document.querySelector(
                                id
                            );

                        if (!target) {
                            return;
                        }

                        event.preventDefault();

                        target.scrollIntoView({
                            behavior: "smooth",
                            block: "start"
                        });
                    }
                );
            });
    }

    /* =====================================================
       CARD ANIMATION
    ===================================================== */

    function animateCards() {

        const cards =
            document.querySelectorAll(
                ".weather-card, .forecast-card, .insight-card, .stat-card"
            );

        cards.forEach(
            (card, index) => {

                card.style.animationDelay =
                    `${index * 60}ms`;

                card.classList.add(
                    "weather-card-visible"
                );
            }
        );
    }

    /* =====================================================
       BUTTON RIPPLE
    ===================================================== */

    function setupButtonRipple() {

        document
            .querySelectorAll(
                "button"
            )
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    function (event) {

                        const ripple =
                            document.createElement(
                                "span"
                            );

                        ripple.className =
                            "button-ripple";

                        const rect =
                            button.getBoundingClientRect();

                        ripple.style.left =
                            `${event.clientX - rect.left}px`;

                        ripple.style.top =
                            `${event.clientY - rect.top}px`;

                        button.appendChild(
                            ripple
                        );

                        setTimeout(
                            () => ripple.remove(),
                            600
                        );
                    }
                );
            });
    }

    /* =====================================================
       ESCAPE HTML
    ===================================================== */

    function escapeHTML(value) {

        if (
            value === undefined ||
            value === null
        ) {
            return "";
        }

        return String(value)
            .replace(
                /&/g,
                "&amp;"
            )
            .replace(
                /</g,
                "&lt;"
            )
            .replace(
                />/g,
                "&gt;"
            )
            .replace(
                /"/g,
                "&quot;"
            )
            .replace(
                /'/g,
                "&#039;"
            );
    }

    /* =====================================================
       KEYBOARD SHORTCUT
       CTRL + SHIFT + R
    ===================================================== */

    function setupKeyboardShortcut() {

        document.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.ctrlKey &&
                    event.shiftKey &&
                    event.key.toLowerCase() === "r"
                ) {

                    event.preventDefault();

                    refreshWeather();
                }
            }
        );
    }

    /* =====================================================
       PUBLIC API
    ===================================================== */

    window.KisanVisionWeather = {

        refresh: refreshWeather,

        load: loadWeather,

        getWeather: () =>
            currentWeather,

        getForecast: () =>
            currentForecast,

        getIntelligence: () =>
            currentIntelligence,

        config: CONFIG
    };

    /* =====================================================
       INITIALIZE
    ===================================================== */

    function initializeWeather() {

        startClock();

        updateGreeting();

        setupRefreshButton();

        setupCitySearch();

        setupNotificationButton();

        setupForecastInteraction();

        setupSmoothScroll();

        setupButtonRipple();

        setupKeyboardShortcut();

        animateCards();

        loadWeather(true);

        startAutoRefresh();
    }

    initializeWeather();

});