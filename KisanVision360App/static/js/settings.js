// =============================
// KisanVision360 Settings JS
// =============================

document.addEventListener("DOMContentLoaded", function () {

    loadTheme();

    loadLanguage();

    loadNotification();

    setupSearch();

});

// =============================
// Dark Mode
// =============================

function toggleTheme() {

    document.body.classList.toggle("dark");

    if (document.body.classList.contains("dark")) {

        localStorage.setItem("theme", "dark");

    } else {

        localStorage.setItem("theme", "light");

    }

}

function loadTheme() {

    let theme = localStorage.getItem("theme");

    if (theme === "dark") {

        document.body.classList.add("dark");

    }

}

// =============================
// Language
// =============================

function changeLanguage() {

    let lang = document.getElementById("language").value;

    localStorage.setItem("language", lang);

    window.location.href = "/change-language/" + lang;

}

function loadLanguage() {

    let lang = localStorage.getItem("language");

    if (lang && document.getElementById("language")) {

        document.getElementById("language").value = lang;

    }

}

// =============================
// Notification
// =============================

function toggleNotification() {

    let status = document.getElementById("notify").checked;

    localStorage.setItem("notification", status);

    fetch("/notification", {

        method: "POST",

        headers: {

            "Content-Type": "application/x-www-form-urlencoded"

        },

        body: "status=" + status

    });

}

function loadNotification() {

    let value = localStorage.getItem("notification");

    if (value == "true") {

        let box = document.getElementById("notify");

        if (box) box.checked = true;

    }

}

// =============================
// Logout
// =============================

function logoutConfirm() {

    if (confirm("Do you really want to logout?")) {

        window.location.href = "/logout";

    }

}

// =============================
// Search Settings
// =============================

function setupSearch() {

    const input = document.getElementById("searchSettings");

    if (!input) return;

    input.addEventListener("keyup", function () {

        let filter = input.value.toLowerCase();

        let cards = document.querySelectorAll(".card");

        cards.forEach(function (card) {

            let text = card.innerText.toLowerCase();

            if (text.includes(filter)) {

                card.style.display = "block";

            } else {

                card.style.display = "none";

            }

        });

    });

}

// =============================
// Success Message
// =============================

function showMessage(msg) {

    alert(msg);

}

// =============================
// Auto Time
// =============================

setInterval(function () {

    let clock = document.getElementById("clock");

    if (clock) {

        let now = new Date();

        clock.innerHTML = now.toLocaleTimeString();

    }

}, 1000);

// =============================
// Weather Refresh
// =============================

function refreshWeather() {

    fetch("/weather/live")

        .then(response => response.json())

        .then(data => {

            let temp = document.getElementById("temp");

            if (temp) {

                temp.innerHTML = data.temperature + "°C";

            }

        });

}
// ================= SETTINGS =================

// Notification Toggle
function toggleNotification() {

    let check = document.getElementById("notify");

    if (check.checked) {

        localStorage.setItem("notification", "ON");

        alert("Notifications Enabled");

    } else {

        localStorage.setItem("notification", "OFF");

        alert("Notifications Disabled");

    }

}


// Load Notification Status
window.onload = function () {

    let status = localStorage.getItem("notification");

    if (status == "OFF") {

        document.getElementById("notify").checked = false;

    }

};


// Language Change
function changeLanguage() {

    let lang = document.getElementById("language").value;

    fetch("/set-language", {

        method: "POST",

        headers: {

            "Content-Type": "application/x-www-form-urlencoded"

        },

        body: "language=" + lang

    })
    .then(() => {

        alert("Language Updated Successfully");

        location.reload();

    });

}


// Search Settings
function searchSettings() {

    let input = document.getElementById("search").value.toLowerCase();

    let cards = document.querySelectorAll(".setting-card");

    cards.forEach(card => {

        if (card.innerText.toLowerCase().includes(input)) {

            card.style.display = "block";

        }

        else {

            card.style.display = "none";

        }

    });

}
