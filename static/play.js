/* =====================================================================
   Vue Partie : état de la table, déverrouillage, notes animateur.
   Les cartes arrivent déjà rendues (recto/verso) dans #deck-data,
   produites par templates/card.html.j2. Ce script ne gère que l'état.
   ===================================================================== */
const DATA = JSON.parse(document.getElementById("deck-data").textContent);
const CARDS = DATA.cards;
const UI = DATA.ui;
const state = {table: new Set(), revealed: new Set(), all: false, notes: false, fresh: null};

const displayId = id => id.endsWith("Qc") ? `${id.slice(0, -2)}cQm` : id.endsWith("Qm") ? `${id.slice(0, -2)}mQc` : id;
const keyHTML = id => `<span class="key">${displayId(id)}</span>`;
const isRevealed = c => state.all || c.lock.length === 0 || state.revealed.has(c.id);

/* Réduit la taille du texte jusqu'à ce qu'il tienne dans la carte. */
function fit(root){
  root.querySelectorAll(".content").forEach(el => {
    el.style.fontSize = "";
    let size = parseFloat(getComputedStyle(el).fontSize), i = 0;
    while (el.scrollHeight > el.clientHeight + 1 && i < 24){ size *= 0.96; el.style.fontSize = size + "px"; i++; }
  });
}

function actionFor(c){
  if (!isRevealed(c)){
    const miss = c.lock.filter(k => !state.table.has(k));
    return miss.length
      ? `<p class="missing">${UI.missing_cards} ${miss.map(keyHTML).join(` ${UI.and_word} `)}</p>`
      : `<button type="button" class="act strong" data-act="reveal" data-id="${c.id}">${UI.reveal_card}</button>`;
  }
  return state.table.has(c.id)
    ? `<button type="button" class="act on" data-act="remove" data-id="${c.id}" aria-pressed="true">${UI.remove_card}</button>`
    : `<button type="button" class="act" data-act="place" data-id="${c.id}" aria-pressed="false">${UI.place_card}</button>`;
}

function slotFor(c){
  const on = state.table.has(c.id);
  const face = isRevealed(c) ? c.recto : c.verso;
  return `<div class="slot${on ? " on" : ""}"><div class="${state.fresh === c.id ? "just-revealed" : ""}">${face}</div>${actionFor(c)}${state.notes && c.note ? `<p class="note">${c.note}</p>` : ""}</div>`;
}

function renderPlay(){
  let html = "";
  DATA.sections.forEach(s => {
    const sectionCards = CARDS.filter(c => c.section === s.key);
    html += `<section class="chain" id="ch-${s.key}"><div class="chain-head"><span class="num">${s.key}</span><div><h2>${s.theme}</h2><p>${s.intention}</p></div></div>`;
    if (s.video) html += `<p class="video-download"><a href="${s.video}" download>${DATA.video_download_label} · ${s.theme} (MP4)</a></p>`;
    if (/^\d+$/.test(s.key)){
      const byType = new Map(sectionCards.map(c => [c.type, c]));
      const stages = [["T", "R"], ["E"], ["Qm", "Qc"], ["M"], ["C"], ["L"]];
      html += `<div class="family-flow">`;
      stages.forEach((types, index) => {
        if (index) html += `<span class="flow-down" aria-hidden="true">↓</span>`;
        html += `<div class="family-row${types.length === 1 ? " single" : ""}">${types.map(type => byType.get(type)).filter(Boolean).map(slotFor).join("")}</div>`;
      });
      html += `</div>`;
    } else {
      html += `<div class="row">${sectionCards.map(slotFor).join("")}</div>`;
    }
    html += `</section>`;
  });
  const play = document.getElementById("play");
  play.innerHTML = html;
  fit(play);
  state.fresh = null;
  const lev = CARDS.filter(c => c.type === "L" && state.table.has(c.id)).length;
  const cardsProgress = UI.cards_progress.replace("{on}", state.table.size).replace("{total}", CARDS.length);
  const leversProgress = (lev === 1 ? UI.lever_progress_one : UI.lever_progress_many)
    .replace("{on}", lev).replace("{total}", DATA.leviers.total);
  const goal = lev >= DATA.leviers.pour_gagner ? ` · ${UI.goal_reached}` : "";
  document.getElementById("progress").textContent = `${cardsProgress} · ${leversProgress}${goal}`;
}

document.getElementById("play").addEventListener("click", e => {
  const b = e.target.closest("button[data-act]"); if (!b) return;
  const id = b.dataset.id, act = b.dataset.act;
  if (act === "reveal"){ state.revealed.add(id); state.fresh = id; }
  if (act === "place") state.table.add(id);
  if (act === "remove") state.table.delete(id);
  renderPlay();
  const again = document.querySelector(`button[data-id="${id}"]`); if (again) again.focus();
});
const tog = (btn, key) => { state[key] = !state[key]; btn.setAttribute("aria-pressed", state[key]); renderPlay(); };
document.getElementById("btn-all").addEventListener("click", e => tog(e.currentTarget, "all"));
document.getElementById("btn-notes").addEventListener("click", e => tog(e.currentTarget, "notes"));
document.getElementById("btn-reset").addEventListener("click", () => {
  state.table.clear(); state.revealed.clear(); state.all = false;
  document.getElementById("btn-all").setAttribute("aria-pressed", "false"); renderPlay();
});

/* Onglets Partie / Impression */
const printRoot = document.getElementById("print-root");
function show(which){
  const isPlay = which === "play";
  const isPrint = !isPlay;
  document.getElementById("tab-play").setAttribute("aria-pressed", isPlay);
  document.getElementById("tab-print-3x3").setAttribute("aria-pressed", which === "print-3x3");
  document.getElementById("tab-print-2x2").setAttribute("aria-pressed", which === "print-2x2");
  document.getElementById("tab-print-2x1").setAttribute("aria-pressed", which === "print-2x1");
  document.getElementById("tab-review").setAttribute("aria-pressed", which === "review");
  document.getElementById("play").style.display = isPlay ? "" : "none";
  document.getElementById("play-ctrls").style.display = isPlay ? "flex" : "none";
  document.getElementById("print-ctrls").style.display = isPrint ? "flex" : "none";
  printRoot.classList.toggle("offscreen", !isPrint);
  const pages = document.getElementById("pages");
  pages.classList.toggle("layout-3x3", which === "print-3x3");
  pages.classList.toggle("layout-2x2", which === "print-2x2");
  pages.classList.toggle("layout-2x1", which === "print-2x1");
  pages.classList.toggle("layout-review", which === "review");
  if (isPrint) fit(pages);
}
document.getElementById("tab-play").addEventListener("click", () => show("play"));
document.getElementById("tab-print-3x3").addEventListener("click", () => show("print-3x3"));
document.getElementById("tab-print-2x2").addEventListener("click", () => show("print-2x2"));
document.getElementById("tab-print-2x1").addEventListener("click", () => show("print-2x1"));
document.getElementById("tab-review").addEventListener("click", () => show("review"));
document.getElementById("btn-print").addEventListener("click", () => { try { window.print(); } catch(e){} });

renderPlay();
const refit = () => { fit(document.getElementById("play")); fit(document.getElementById("pages")); };
if (document.fonts && document.fonts.ready) document.fonts.ready.then(refit);
window.addEventListener("load", refit);
window.addEventListener("beforeprint", () => fit(document.getElementById("pages")));
