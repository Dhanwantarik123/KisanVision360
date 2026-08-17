// ================================
// KisanVision360 Smart Irrigation
// ================================

document.addEventListener("DOMContentLoaded", function () {

    animateCards();

    calculateSuggestion();

});

// ================================
// Card Animation
// ================================

function animateCards() {

    const cards = document.querySelectorAll(".card,.form-card,.ai-card,.result-card");

    cards.forEach((card, index) => {

        card.style.opacity = "0";
        card.style.transform = "translateY(40px)";

        setTimeout(() => {

            card.style.transition = ".6s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0px)";

        }, index * 150);

    });

}

// ================================
// Form Validation
// ================================

const form = document.querySelector("form");

if(form){

form.addEventListener("submit",function(e){

let crop=document.querySelector("input[name='crop']").value.trim();

let rainfall=document.querySelector("input[name='rainfall']").value;

if(crop===""){

alert("Please enter crop name.");
e.preventDefault();
return;

}

if(rainfall<0){

alert("Rainfall cannot be negative.");
e.preventDefault();

}

});

}

// ================================
// AI Suggestion
// ================================

function calculateSuggestion(){

const crop=document.querySelector("input[name='crop']");
const soil=document.querySelector("select[name='soil']");
const rain=document.querySelector("input[name='rainfall']");

if(!crop) return;

[crop,soil,rain].forEach(el=>{

el.addEventListener("input",updateRecommendation);

});

}

function updateRecommendation(){

const soil=document.querySelector("select[name='soil']").value;

const rainfall=parseFloat(document.querySelector("input[name='rainfall']").value)||0;

let message="";
let duration="";
let water="";

if(rainfall>50){

message="No irrigation required today.";
duration="0 Minutes";
water="Very Low";

}

else if(soil==="dry"){

message="Immediate irrigation recommended.";
duration="35 Minutes";
water="High";

}

else if(soil==="normal"){

message="Moderate irrigation required.";
duration="20 Minutes";
water="Medium";

}

else{

message="No immediate irrigation.";
duration="10 Minutes";
water="Low";

}

const recommend=document.querySelectorAll(".recommend");

if(recommend.length>=3){

recommend[0].innerHTML="<strong>Recommendation</strong><br>"+message;

recommend[1].innerHTML="<strong>Duration</strong><br>"+duration;

recommend[2].innerHTML="<strong>Water Requirement</strong><br>"+water;

}

}

// ================================
// Progress Animation
// ================================

const statValues=document.querySelectorAll(".card h2");

statValues.forEach(stat=>{

let text=stat.innerText;

if(text.includes("%")){

let target=parseInt(text);

let count=0;

let timer=setInterval(()=>{

count++;

stat.innerHTML=count+"%";

if(count>=target){

clearInterval(timer);

}

},20);

}

});

// ================================
// Loading Button
// ================================

const submitBtn=document.querySelector("button[type='submit']");

if(submitBtn){

submitBtn.addEventListener("click",()=>{

submitBtn.innerHTML='<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

});

}

// ================================
// Chatbot
// ================================

function toggleChat(){

const box=document.getElementById("chatBox");

if(!box) return;

if(box.style.display==="block"){

box.style.display="none";

}else{

box.style.display="block";

}

}

function sendMessage(){

const input=document.getElementById("userMessage");

const body=document.getElementById("chatBody");

if(!input||!body) return;

let msg=input.value.trim();

if(msg==="") return;

body.innerHTML+=`
<div style="text-align:right;margin:10px;">
<div style="display:inline-block;background:#18a74b;color:white;padding:10px 15px;border-radius:15px;">
${msg}
</div>
</div>
`;

setTimeout(()=>{

body.innerHTML+=`
<div style="margin:10px;">
<div style="display:inline-block;background:#eef7ef;padding:10px 15px;border-radius:15px;">
💧 AI Recommendation:<br>
Check soil moisture before irrigation. Early morning watering is recommended.
</div>
</div>
`;

body.scrollTop=body.scrollHeight;

},700);

input.value="";

}

// ================================
// Live Clock
// ================================

setInterval(()=>{

const clock=document.getElementById("liveClock");

if(clock){

const d=new Date();

clock.innerHTML=d.toLocaleTimeString();

}

},1000);

// ================================
// Weather Color Change
// ================================

const hero=document.querySelector(".hero");

if(hero){

const hour=new Date().getHours();

if(hour>=18){

hero.style.background="linear-gradient(135deg,#0d5b2d,#063b1b)";

}

}

// ================================
// Smooth Scroll
// ================================

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
