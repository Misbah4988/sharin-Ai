const form = document.querySelector("#composer");
const input = document.querySelector("#message");
const chat = document.querySelector("#chat");
const statusLabel = document.querySelector("#status");
const sendButton = document.querySelector("#send");
const micButton = document.querySelector("#mic");
const speakToggle = document.querySelector("#speak");
const history = [];

function setStatus(text){ statusLabel.textContent = text; }
function addMessage(who, text){
  const article = document.createElement("article");
  article.className = `message ${who === "You" ? "user" : "assistant"}`;
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = who === "You" ? "Y" : "◇";
  const wrap = document.createElement("div");
  wrap.className = "bubble-wrap";
  const speaker = document.createElement("div");
  speaker.className = "speaker";
  speaker.textContent = who === "You" ? "YOU" : "SHARIN";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.append(speaker, bubble); article.append(avatar, wrap); chat.append(article);
  chat.scrollTop = chat.scrollHeight;
}
function speak(text){
  if(!speakToggle.checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  window.speechSynthesis.speak(utterance);
}
async function sendMessage(raw){
  const message = raw.trim();
  if(!message || sendButton.disabled) return;
  addMessage("You", message);
  input.value = ""; input.style.height = "auto";
  sendButton.disabled = true; setStatus("Thinking...");
  try{
    const response = await fetch("/api/chat", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message, history})
    });
    const data = await response.json();
    if(!response.ok) throw new Error(data.detail || "Request failed. Please try again.");
    const answer = data.answer || "I didn't receive a response.";
    addMessage("Sharin", answer);
    history.push({role:"user", content:message}, {role:"assistant", content:answer});
    if(history.length > 32) history.splice(0, history.length - 32);
    speak(answer);
  }catch(error){
    addMessage("Sharin", `Sorry, I couldn't complete that request. ${error.message}`);
  }finally{
    sendButton.disabled = false; setStatus("Ready"); input.focus();
  }
}
form.addEventListener("submit", e => {e.preventDefault(); sendMessage(input.value);});
input.addEventListener("input", () => {input.style.height="auto"; input.style.height=Math.min(input.scrollHeight,180)+"px";});
input.addEventListener("keydown", e => {
  if(e.key === "Enter" && !e.shiftKey && !e.isComposing){e.preventDefault(); form.requestSubmit();}
});
document.querySelectorAll("[data-prompt]").forEach(button => button.addEventListener("click",()=>sendMessage(button.dataset.prompt)));
document.querySelectorAll("[data-open]").forEach(button => button.addEventListener("click",()=>window.open(button.dataset.open,"_blank","noopener,noreferrer")));
document.querySelector("#downloadText").addEventListener("click",()=>{
  const text = [...chat.querySelectorAll(".message")].map(m => {
    const who = m.classList.contains("user") ? "You" : "Sharin";
    return `${who}: ${m.querySelector(".bubble").innerText}`;
  }).join("\n\n");
  const url = URL.createObjectURL(new Blob([text],{type:"text/plain;charset=utf-8"}));
  const a = document.createElement("a"); a.href=url; a.download="sharin-conversation.txt"; a.click();
  URL.revokeObjectURL(url);
});
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if(!SpeechRecognition){
  micButton.title = "Voice input is not supported in this browser";
  micButton.addEventListener("click",()=>addMessage("Sharin","Voice input isn't supported by this browser. Try a current version of Chrome or Edge, or type your message."));
}else{
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US"; recognition.interimResults = false; recognition.maxAlternatives = 1;
  micButton.addEventListener("click",()=>{
    try{setStatus("Listening..."); recognition.start();}catch(e){setStatus("Ready");}
  });
  recognition.onresult = event => {input.value = event.results[0][0].transcript; setStatus("Ready"); form.requestSubmit();};
  recognition.onerror = () => {setStatus("Ready"); addMessage("Sharin","I couldn't capture your speech. Check microphone permission and try again.");};
  recognition.onend = () => {if(statusLabel.textContent==="Listening...")setStatus("Ready");};
}
