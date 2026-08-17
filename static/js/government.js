// =============================
// Live Search
// =============================

const searchInput = document.getElementById("searchInput");

if(searchInput){

searchInput.addEventListener("keyup",function(){

let value=this.value.toLowerCase();

let cards=document.querySelectorAll(".scheme-card");

cards.forEach(function(card){

let text=card.innerText.toLowerCase();

if(text.includes(value))
{
card.style.display="block";
}
else
{
card.style.display="none";
}

});

});

}



// =============================
// Category Filter
// =============================

function filterSchemes(category){

let cards=document.querySelectorAll(".scheme-card");

let buttons=document.querySelectorAll(".filter-btn");


buttons.forEach(btn=>btn.classList.remove("active"));

event.target.classList.add("active");


cards.forEach(card=>{

if(category=="all")
{
card.style.display="block";
}
else
{
if(card.dataset.category===category)
{
card.style.display="block";
}
else
{
card.style.display="none";
}
}

});

}