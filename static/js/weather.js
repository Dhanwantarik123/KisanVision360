// =======================================
// KisanVision360 Weather Dashboard
// =======================================

document.addEventListener("DOMContentLoaded", () => {

    animateCards();
    updateClock();
    weatherGreeting();
    startCounters();

});

/* ===============================
   CARD ANIMATION
================================ */

function animateCards(){

const cards=document.querySelectorAll(
'.stat-card,.forecast-card,.action-card,.weather-mini,.ai-card,.tips-card'
);

cards.forEach((card,index)=>{

card.style.opacity="0";
card.style.transform="translateY(40px)";

setTimeout(()=>{

card.style.transition="0.6s";
card.style.opacity="1";
card.style.transform="translateY(0px)";

},index*120);

});

}

/* ===============================
   LIVE CLOCK
================================ */

function updateClock(){

const clock=document.getElementById("liveClock");

if(!clock) return;

setInterval(()=>{

const now=new Date();

clock.innerHTML=now.toLocaleTimeString();

},1000);

}

/* ===============================
   WEATHER GREETING
================================ */

function weatherGreeting(){

const title=document.querySelector(".topbar h1");

if(!title) return;

const hour=new Date().getHours();

let greet="";

if(hour<12){

greet="☀️ Good Morning";

}

else if(hour<17){

greet="🌤 Good Afternoon";

}

else{

greet="🌙 Good Evening";

}

title.innerHTML=greet+" | Live Weather Dashboard";

}

/* ===============================
   COUNTER ANIMATION
================================ */

function startCounters(){

document.querySelectorAll(".stat-card h2").forEach(counter=>{

let value=parseInt(counter.innerText);

if(isNaN(value)) return;

let current=0;

let timer=setInterval(()=>{

current++;

counter.innerHTML=current;

if(current>=value){

clearInterval(timer);

}

},20);

});

}

/* ===============================
   SEARCH
================================ */

const search=document.querySelector(".search-box input");

if(search){

search.addEventListener("keyup",function(){

console.log("Searching:",this.value);

});

}

/* ===============================
   BUTTON RIPPLE
================================ */

document.querySelectorAll("button").forEach(btn=>{

btn.addEventListener("click",function(e){

let circle=document.createElement("span");

let x=e.offsetX;
let y=e.offsetY;

circle.style.left=x+"px";
circle.style.top=y+"px";

circle.classList.add("ripple");

this.appendChild(circle);

setTimeout(()=>{

circle.remove();

},600);

});

});

/* ===============================
   WEATHER COLOR
================================ */

const hero=document.querySelector(".weather-hero");

if(hero){

const temp=document.querySelector(".weather-left h1");

if(temp){

let t=parseInt(temp.innerText);

if(t>=40){

hero.style.background="linear-gradient(135deg,#ff5722,#ff9800)";

}

else if(t>=30){

hero.style.background="linear-gradient(135deg,#1fa64b,#0b7d38)";

}

else{

hero.style.background="linear-gradient(135deg,#2196f3,#00bcd4)";

}

}

}

/* ===============================
   NOTIFICATION
================================ */

const notify=document.querySelector(".notification");

if(notify){

notify.onclick=function(){

alert("No new notifications.");

}

}

/* ===============================
   SMOOTH SCROLL
================================ */

document.querySelectorAll("a").forEach(anchor=>{

anchor.addEventListener("click",function(e){

let href=this.getAttribute("href");

if(href && href.startsWith("#")){

e.preventDefault();

document.querySelector(href).scrollIntoView({

behavior:"smooth"

});

}

});

});

/* ===============================
   WEATHER REFRESH
================================ */

setInterval(()=>{

console.log("Weather Updated");

},600000);