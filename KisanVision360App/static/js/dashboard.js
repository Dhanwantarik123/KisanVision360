// =============================
// KisanVision360 Dashboard JS
// =============================

// Live Clock
function updateClock() {
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

    const clock = document.getElementById("clock");

    if (clock) {
        clock.innerHTML = now.toLocaleString("en-IN", options);
    }
}

setInterval(updateClock, 1000);
updateClock();


// Card Hover Animation

const cards = document.querySelectorAll(".card");

cards.forEach(card => {

    card.addEventListener("mouseenter", () => {

        card.style.transform = "translateY(-10px) scale(1.03)";

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform = "translateY(0px) scale(1)";

    });

});


// Active Sidebar Menu

const menuItems = document.querySelectorAll(".sidebar li");

menuItems.forEach(item => {

    item.addEventListener("click", () => {

        menuItems.forEach(menu => {

            menu.classList.remove("active");

        });

        item.classList.add("active");

    });

});


// Counter Animation

function animateValue(element, start, end, duration) {

    if (!element) return;

    let range = end - start;

    let current = start;

    let increment = end > start ? 1 : -1;

    let stepTime = Math.abs(Math.floor(duration / range));

    let timer = setInterval(() => {

        current += increment;

        element.innerHTML = current + "%";

        if (current == end) {

            clearInterval(timer);

        }

    }, stepTime);

}

const health = document.querySelector(".progress-bar");

if (health) {

    let value = parseInt(health.innerHTML);

    health.innerHTML = "0%";

    animateValue(health, 0, value, 1500);

}


// Auto Refresh Weather Every 10 Minutes

function refreshWeather() {

    fetch("/weather/Mumbai")

        .then(response => response.json())

        .then(data => {

            console.log("Weather Updated");

            console.log(data);

            // You can update weather card values here
            // Example:
            //
            // document.getElementById("temp").innerHTML =
            // data.temperature + "°C";

        })

        .catch(error => {

            console.log(error);

        });

}

setInterval(refreshWeather, 600000);


// Notification Popup

function showNotification(message) {

    let div = document.createElement("div");

    div.className = "notification-popup";

    div.innerHTML = message;

    document.body.appendChild(div);

    setTimeout(() => {

        div.classList.add("show");

    }, 100);

    setTimeout(() => {

        div.classList.remove("show");

        setTimeout(() => {

            div.remove();

        }, 500);

    }, 4000);

}


// Welcome Notification

window.onload = () => {

    showNotification("🌾 Welcome to KisanVision360 Dashboard");

};


// Scroll Animation

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {

            entry.target.classList.add("animate");

        }

    });

});

document.querySelectorAll(".card,.analytics-card,.section").forEach(el => {

    observer.observe(el);

});


// Dark Mode Toggle (Optional)

function toggleDarkMode() {

    document.body.classList.toggle("dark");

    localStorage.setItem(

        "theme",

        document.body.classList.contains("dark") ? "dark" : "light"

    );

}

if (localStorage.getItem("theme") === "dark") {

    document.body.classList.add("dark");

}


// Smooth Scroll

document.querySelectorAll("a[href^='#']").forEach(anchor => {

    anchor.addEventListener("click", function (e) {

        e.preventDefault();

        document.querySelector(this.getAttribute("href"))

            .scrollIntoView({

                behavior: "smooth"

            });

    });

});
