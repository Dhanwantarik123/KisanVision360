function sendMessage(){


let input=document.getElementById("message");

let message=input.value;


if(message=="")
return;



let box=document.getElementById("chat-box");



box.innerHTML +=

`
<div class="user">
${message}
</div>
`;



fetch("/ask_chatbot",
{

method:"POST",

headers:
{
"Content-Type":"application/json"
},


body:
JSON.stringify(
{
message:message
}
)

})


.then(response=>response.json())


.then(data=>{


box.innerHTML +=

`
<div class="bot">
${data.reply}
</div>
`;



box.scrollTop=box.scrollHeight;


});



input.value="";


}
