
// ==========================================
// QUIZMASTER - APLICACIÓN PRINCIPAL
// ==========================================

let allGames = [];
let selectedGame = null;

let currentMatch = null;
let currentQuestionData = null;
let selectedAnswer = null;
let selectedTargetIds = [];

const defaultTeamNames = [
    "Leones", "Tigres", "Águilas", "Lobos", "Panteras",
    "Delfines", "Halcones", "Dragones", "Zorros", "Osos"
];

const teamAvatars = [
    "🦁", "🐯", "🦅", "🐺", "🐆",
    "🐬", "🦅", "🐉", "🦊", "🐻",
    "🐼", "🦈", "🦄", "🐵", "🐸"
];

const teamColors = [
    "#6C5CE7", "#E67E22", "#00B894", "#0984E3", "#E84393",
    "#FDCB6E", "#D63031", "#00CEC9", "#636E72", "#A29BFE"
];


// ==========================================
// CAMBIAR DE PANTALLA
// ==========================================

function showView(view) {

    const views = ["home", "library", "create", "setup", "game"];

    views.forEach(name => {
        const element = document.getElementById(`${name}-view`);

        if (element) {
            element.hidden = name !== view;
        }
    });

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

    if (view === "library") loadGames();
    if (view === "setup") renderTeamSetup();
}


// ==========================================
// SEGURIDAD HTML
// ==========================================

function escapeHTML(value) {

    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);

}


// ==========================================
// CARGAR BIBLIOTECA
// ==========================================

async function loadGames() {

    const grid = document.getElementById("games-grid");
    const message = document.getElementById("library-message");

    message.textContent = "Cargando biblioteca...";
    grid.innerHTML = "";

    try {

        const response = await fetch("/api/games/");

        if (!response.ok) {
            throw new Error("No se pudo consultar la biblioteca.");
        }

        allGames = await response.json();

        message.textContent =
            `${allGames.length} juego(s) guardado(s).`;

        filterGames();

    } catch (error) {
        message.textContent = "Error: " + error.message;
    }

}


// ==========================================
// FILTRAR JUEGOS
// ==========================================

function filterGames() {

    const search = document
        .getElementById("game-search")
        .value
        .toLowerCase()
        .trim();

    const filtered = allGames.filter(game =>
        game.title.toLowerCase().includes(search) ||
        (game.topic || "").toLowerCase().includes(search)
    );

    renderGames(filtered);
}


// ==========================================
// MOSTRAR JUEGOS
// ==========================================

function renderGames(games) {

    const grid = document.getElementById("games-grid");

    grid.innerHTML = "";

    if (games.length === 0) {

        grid.innerHTML = `
            <div class="empty-library">
                <div class="empty-icon">🎮</div>
                <h2>TODAVÍA NO HAY JUEGOS</h2>
                <p>
                    Crea tu primer concurso y empieza a llenar tu biblioteca.
                </p>
                <button class="primary" onclick="showView('create')">
                    + CREAR MI PRIMER JUEGO
                </button>
            </div>
        `;

        return;
    }

    games.forEach(game => {

        const card = document.createElement("article");

        card.className = "game-card";

        card.innerHTML = `
            <div class="game-card-top">
                <span class="game-icon">🎯</span>
                <span class="difficulty">
                    ${escapeHTML(game.difficulty)}
                </span>
            </div>

            <h2>${escapeHTML(game.title)}</h2>

            <p class="game-topic">
                ${escapeHTML(game.topic || "Sin temática")}
            </p>

            <div class="game-card-info">
                <span>❓ ${Number(game.questions_count) || 0} preguntas</span>
                <span>QUIZMASTER</span>
            </div>

            <div class="game-card-actions">
                <button
                    class="primary"
                    onclick="prepareGame(${Number(game.id)})"
                >
                    JUGAR
                </button>

                <button
                    class="delete-button"
                    onclick="deleteGame(${Number(game.id)})"
                >
                    ELIMINAR
                </button>
            </div>
        `;

        grid.appendChild(card);
    });
}


// ==========================================
// CREAR JUEGO - PROTEGIDO CON CONTRASEÑA
// ==========================================

document
    .getElementById("create-game-form")
    .addEventListener("submit", async function(event) {

        event.preventDefault();

        const message = document.getElementById("create-message");

        const game = {
            title: document.getElementById("game-title").value.trim(),
            topic: document.getElementById("game-topic").value.trim(),
            difficulty: document.getElementById("game-difficulty").value
        };

        if (!game.title) {
            message.textContent = "Debes introducir un título.";
            return;
        }

        const password = prompt(
            "Introduce la contraseña de administración para crear el juego:"
        );

        if (password === null || password.length === 0) {
            message.textContent = "Creación cancelada.";
            return;
        }

        message.textContent = "Comprobando autorización...";

        try {

            const response = await fetch("/api/games/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Admin-Password": password
                },
                body: JSON.stringify(game)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || "No se pudo guardar.");
            }

            this.reset();

            message.textContent = "¡Juego guardado correctamente!";

            await loadGames();

            showView("library");

        } catch (error) {
            message.textContent = "Error: " + error.message;
        }
    });


// ==========================================
// ELIMINAR JUEGO - PROTEGIDO CON CONTRASEÑA
// ==========================================

async function deleteGame(id) {

    const confirmed = confirm(
        "¿Seguro que quieres eliminar este juego y sus preguntas?"
    );

    if (!confirmed) return;

    const password = prompt(
        "Introduce la contraseña de administración para eliminar el juego:"
    );

    if (password === null || password.length === 0) return;

    try {

        const response = await fetch(`/api/games/${id}`, {
            method: "DELETE",
            headers: {
                "X-Admin-Password": password
            }
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "No se pudo eliminar.");
        }

        alert("Juego eliminado correctamente.");

        await loadGames();

    } catch (error) {
        alert("Error: " + error.message);
    }
}


// ==========================================
// SELECCIONAR JUEGO
// ==========================================

function prepareGame(id) {

    selectedGame = allGames.find(
        game => Number(game.id) === Number(id)
    );

    if (!selectedGame) {
        alert("No se ha encontrado el juego seleccionado.");
        return;
    }

    const questionCount = Number(selectedGame.questions_count) || 0;

    if (questionCount === 0) {
        alert("Este juego todavía no tiene preguntas.");
        return;
    }

    document.getElementById("setup-game-title").textContent =
        selectedGame.title;

    document.getElementById("setup-game-topic").textContent =
        selectedGame.topic || "Sin temática";

    document.getElementById("team-count").value = "3";

    renderTeamSetup();

    showView("setup");
}


// ==========================================
// GENERAR TARJETAS DE EQUIPOS
// ==========================================

function renderTeamSetup() {

    const grid = document.getElementById("teams-setup-grid");
    const countSelect = document.getElementById("team-count");

    if (!grid || !countSelect) return;

    const count = Number(countSelect.value) || 3;

    grid.innerHTML = "";

    for (let i = 0; i < count; i++) {

        const card = document.createElement("article");

        card.className = "team-setup-card";

        const avatarOptions = teamAvatars.map(avatar => `
            <option value="${avatar}" ${avatar === teamAvatars[i] ? "selected" : ""}>
                ${avatar}
            </option>
        `).join("");

        card.innerHTML = `

            <div class="team-setup-header">
                <span class="team-number">EQUIPO ${i + 1}</span>
                <span class="team-default-score">⭐ 100 PUNTOS</span>
            </div>

            <div class="team-avatar-preview" id="team-preview-${i}">
                ${teamAvatars[i]}
            </div>

            <label for="team-name-${i}">
                NOMBRE DEL EQUIPO
            </label>

            <input
                type="text"
                id="team-name-${i}"
                value="${escapeHTML(defaultTeamNames[i])}"
                maxlength="100"
                required
            >

            <label for="team-avatar-${i}">
                AVATAR
            </label>

            <select
                id="team-avatar-${i}"
                onchange="updateTeamAvatar(${i})"
            >
                ${avatarOptions}
            </select>

            <label for="team-color-${i}">
                COLOR DEL EQUIPO
            </label>

            <input
                type="color"
                id="team-color-${i}"
                value="${teamColors[i]}"
            >

        `;

        grid.appendChild(card);
    }

    const message = document.getElementById("setup-message");

    if (message) message.textContent = "";
}


// ==========================================
// ACTUALIZAR AVATAR
// ==========================================

function updateTeamAvatar(index) {

    const avatar = document.getElementById(`team-avatar-${index}`).value;

    document.getElementById(`team-preview-${index}`).textContent = avatar;
}


// ==========================================
// CAMBIAR NÚMERO DE EQUIPOS
// ==========================================

document
    .getElementById("team-count")
    .addEventListener("change", renderTeamSetup);


// ==========================================
// CREAR PARTIDA
// ==========================================

async function startMatch() {

    const message = document.getElementById("setup-message");

    if (!selectedGame) {
        message.textContent = "No hay ningún juego seleccionado.";
        return;
    }

    const count = Number(document.getElementById("team-count").value);

    const teams = [];

    for (let i = 0; i < count; i++) {

        const name = document
            .getElementById(`team-name-${i}`)
            .value.trim();

        const avatar = document
            .getElementById(`team-avatar-${i}`)
            .value;

        const color = document
            .getElementById(`team-color-${i}`)
            .value;

        if (!name) {
            message.textContent =
                `Debes introducir el nombre del equipo ${i + 1}.`;
            return;
        }

        teams.push({ name, avatar, color });
    }

    const names = teams.map(team => team.name.toLowerCase());

    if (new Set(names).size !== names.length) {
        message.textContent =
            "No puede haber dos equipos con el mismo nombre.";
        return;
    }

    const button = document.querySelector("#setup-view button.primary");

    button.disabled = true;
    message.textContent = "Creando partida...";

    try {

        const response = await fetch("/api/matches/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                game_id: selectedGame.id,
                teams: teams
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "No se pudo crear la partida.");
        }

        currentMatch = result;

        console.log("PARTIDA CREADA:", result);

        await openMatch(result.match_id);

    } catch (error) {

        message.textContent =
            "Error al crear la partida: " + error.message;

    } finally {
        button.disabled = false;
    }
}


// ==========================================
// ABRIR TABLERO
// ==========================================

async function openMatch(matchId) {

    currentMatch = {
        ...currentMatch,
        match_id: matchId
    };

    selectedAnswer = null;
    selectedTargetIds = [];

    document.getElementById("match-game-title").textContent =
        currentMatch.game_title || selectedGame?.title || "Partida";

    document.getElementById("answer-result").hidden = true;
    document.getElementById("final-results").hidden = true;

    ensureSubmitButton();

    showView("game");

    await loadCurrentQuestion();
}


// ==========================================
// CARGAR PREGUNTA ACTUAL
// ==========================================

async function loadCurrentQuestion() {

    if (!currentMatch?.match_id) return;

    const message = document.getElementById("answer-message");

    message.textContent = "Cargando pregunta...";

    try {

        const response = await fetch(
            `/api/matches/${currentMatch.match_id}/current-question`
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "No se pudo cargar la pregunta.");
        }

        currentQuestionData = result;

        selectedAnswer = null;
        selectedTargetIds = [];

        document.getElementById("answer-result").hidden = true;
        document.getElementById("final-results").hidden = true;

        renderCurrentQuestion(result);

        message.textContent = "";

    } catch (error) {
        message.textContent = "Error: " + error.message;
    }
}


// ==========================================
// MOSTRAR PREGUNTA Y TURNO
// ==========================================

function renderCurrentQuestion(data) {

    const question = data.question;
    const activeTeam = data.active_team;

    if (!question || !activeTeam) {
        throw new Error("La API no ha devuelto una pregunta o equipo activo.");
    }

    document.getElementById("question-number").textContent =
        `${data.question_number} / ${data.total_questions}`;

    document.getElementById("match-progress").textContent =
        `PREGUNTA ${data.question_number} DE ${data.total_questions}`;

    document.getElementById("question-text").textContent = question.text;

    document.getElementById("option-a").textContent = question.option_a;
    document.getElementById("option-b").textContent = question.option_b;
    document.getElementById("option-c").textContent = question.option_c;
    document.getElementById("option-d").textContent = question.option_d;

    document.getElementById("active-team-avatar").textContent =
        activeTeam.avatar || "🎮";

    document.getElementById("active-team-name").textContent =
        activeTeam.name;

    document.getElementById("active-team-avatar").style.backgroundColor =
        activeTeam.color || "#6C5CE7";

    const imageContainer = document.getElementById("question-image-container");
    const questionImage = document.getElementById("question-image");

    if (question.image_path) {

        questionImage.src =
            question.image_path.startsWith("http") ||
            question.image_path.startsWith("/")
                ? question.image_path
                : `/${question.image_path}`;

        imageContainer.hidden = false;

    } else {

        questionImage.removeAttribute("src");
        imageContainer.hidden = true;

    }

    renderScoreboard(currentMatch.teams || []);

    renderTargetTeams(data.available_targets || []);

    document.querySelectorAll(".answer-option").forEach(button => {
        button.disabled = false;
        button.classList.remove("selected", "correct", "incorrect");
    });

    const submitButton = document.getElementById("submit-answer-button");

    if (submitButton) {
        submitButton.disabled = false;
        submitButton.hidden = false;
    }
}


// ==========================================
// MARCADOR
// ==========================================

function renderScoreboard(teams) {

    const container = document.getElementById("match-scoreboard");

    container.innerHTML = "";

    teams.forEach(team => {

        const card = document.createElement("article");

        card.className = "match-team-card";
        card.style.borderColor = team.color || "#6C5CE7";

        card.innerHTML = `
            <div class="match-team-avatar">
                ${escapeHTML(team.avatar || "🎮")}
            </div>

            <div class="match-team-name">
                ${escapeHTML(team.name)}
            </div>

            <div class="match-team-score">
                ${Number(team.score)} <small>PTS</small>
            </div>
        `;

        container.appendChild(card);
    });
}


// ==========================================
// MOSTRAR EQUIPOS OBJETIVO
// ==========================================

function renderTargetTeams(teams) {

    const container = document.getElementById("target-team-grid");

    container.innerHTML = "";

    teams.forEach(team => {

        const label = document.createElement("label");

        label.className = "target-team-card";

        const teamColor = team.color || "#6C5CE7";

        label.style.setProperty("--team-color", teamColor);
        label.style.borderColor = teamColor;

        label.innerHTML = `
            <input
                type="checkbox"
                value="${Number(team.id)}"
                onchange="toggleTargetTeam(${Number(team.id)}, this.checked)"
            >

            <span class="target-team-avatar">
                ${escapeHTML(team.avatar || "🎮")}
            </span>

            <span class="target-team-name">
                ${escapeHTML(team.name)}
            </span>

            <span class="target-team-score">
                ${Number(team.score)}
                <small>PUNTOS</small>
            </span>

            <span class="target-team-select-label">
                SELECCIONAR RIVAL
            </span>
        `;

        container.appendChild(label);
    });
}


// ==========================================
// SELECCIONAR EQUIPOS RIVALES
// ==========================================

function toggleTargetTeam(teamId, checked) {

    if (checked) {

        if (!selectedTargetIds.includes(teamId)) {
            selectedTargetIds.push(teamId);
        }

    } else {

        selectedTargetIds = selectedTargetIds.filter(
            id => id !== teamId
        );
    }
}


// ==========================================
// SELECCIONAR RESPUESTA
// ==========================================

function selectAnswer(option) {

    selectedAnswer = option;

    document.querySelectorAll(".answer-option").forEach(button => {

        button.classList.toggle(
            "selected",
            button.dataset.option === option
        );

    });
}


// ==========================================
// BOTÓN PARA CONFIRMAR RESPUESTA
// ==========================================

function ensureSubmitButton() {

    if (document.getElementById("submit-answer-button")) return;

    const targetPanel = document.querySelector(".target-panel");

    const button = document.createElement("button");

    button.type = "button";
    button.id = "submit-answer-button";
    button.className = "primary";
    button.textContent = "CONFIRMAR RESPUESTA";
    button.onclick = submitAnswer;

    targetPanel.appendChild(button);
}


// ==========================================
// ENVIAR RESPUESTA AL BACKEND
// ==========================================

async function submitAnswer() {

    const message = document.getElementById("answer-message");

    if (!selectedAnswer) {
        message.textContent = "Primero debes seleccionar una respuesta.";
        return;
    }

    if (selectedTargetIds.length === 0) {
        message.textContent = "Debes seleccionar al menos un equipo rival.";
        return;
    }

    const button = document.getElementById("submit-answer-button");

    button.disabled = true;

    message.textContent = "Registrando respuesta...";

    try {

        const response = await fetch(
            `/api/matches/${currentMatch.match_id}/answer`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    selected_option: selectedAnswer,
                    targeted_team_ids: selectedTargetIds
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "No se pudo registrar la respuesta.");
        }

        console.log("RESPUESTA REGISTRADA:", result);

        renderAnswerResult(result);

        message.textContent = "";

    } catch (error) {

        message.textContent = "Error: " + error.message;
        button.disabled = false;

    }
}


// ==========================================
// MOSTRAR RESULTADO Y PUNTUACIONES
// ==========================================

function renderAnswerResult(result) {

    const resultPanel = document.getElementById("answer-result");

    resultPanel.hidden = false;

    const title = document.getElementById("answer-result-title");

    if (result.is_correct) {

        title.textContent = "🎉 ¡RESPUESTA CORRECTA!";
        title.className = "answer-result-title correct";

    } else {

        title.textContent = "❌ RESPUESTA INCORRECTA";
        title.className = "answer-result-title incorrect";

    }

    document.getElementById("correct-answer").textContent =
        `La respuesta correcta era: ${result.correct_option}`;

    document.getElementById("answer-explanation").textContent =
        result.explanation || "No hay explicación disponible.";

    document.querySelectorAll(".answer-option").forEach(button => {

        button.disabled = true;

        const option = button.dataset.option;

        if (option === result.correct_option) {
            button.classList.add("correct");
        }

        if (
            option === result.selected_option &&
            !result.is_correct
        ) {
            button.classList.add("incorrect");
        }

    });

    const changesContainer = document.getElementById("score-changes");

    changesContainer.innerHTML = "";

    (result.score_changes || []).forEach(change => {

        const row = document.createElement("div");

        row.className = "score-change-row";

        const points = Number(change.points);
        const sign = points > 0 ? "+" : "";

        row.innerHTML = `
            <span>${escapeHTML(change.team_name)}</span>
            <strong>${sign}${points} puntos</strong>
            <span>Nuevo total: ${Number(change.new_score)}</span>
        `;

        changesContainer.appendChild(row);
    });

    if (result.ranking) {
        currentMatch.teams = result.ranking;
        renderScoreboard(result.ranking);
    }

    const submitButton = document.getElementById("submit-answer-button");

    if (submitButton) submitButton.hidden = true;

    document.getElementById("target-team-grid")
        .querySelectorAll("input")
        .forEach(input => {
            input.disabled = true;
        });

    if (result.finished || result.status === "completed") {

        document.getElementById("next-question-button").hidden = true;

        renderFinalResults(result);

    } else {

        document.getElementById("next-question-button").hidden = false;

    }

    resultPanel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ==========================================
// SIGUIENTE PREGUNTA
// ==========================================

async function nextQuestion() {

    document.getElementById("answer-result").hidden = true;

    await loadCurrentQuestion();

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// ==========================================
// RESULTADOS FINALES - PODIO
// ==========================================

function renderFinalResults(result) {

    const finalPanel = document.getElementById("final-results");

    finalPanel.hidden = false;

    const winnerContainer = document.getElementById("winner-announcement");
    const scoreboard = document.getElementById("final-scoreboard");

    const ranking = [...(result.ranking || currentMatch.teams || [])]
        .sort((a, b) => Number(b.score) - Number(a.score));

    winnerContainer.innerHTML = "";
    scoreboard.innerHTML = "";

    if (ranking.length === 0) {
        winnerContainer.textContent = "Partida finalizada.";
        return;
    }

    const medals = ["🥇", "🥈", "🥉"];

    const podiumColors = ["#D6A629", "#9CA3AF", "#B77952"];
    const podiumHeights = ["190px", "145px", "115px"];

    const winner = ranking[0];

    winnerContainer.innerHTML = `
        <div style="
            text-align:center;
            padding:25px 15px;
            margin-bottom:25px;
            border-radius:22px;
            background:linear-gradient(135deg,#30245F,#6546C8);
            color:white;
            box-shadow:0 12px 35px rgba(0,0,0,0.20);
        ">
            <div style="font-size:48px;margin-bottom:8px;">🏆</div>

            <div style="
                font-size:15px;
                font-weight:800;
                letter-spacing:3px;
                margin-bottom:12px;
            ">
                ¡TENEMOS GANADORES!
            </div>

            <div style="
                font-size:clamp(28px,5vw,48px);
                font-weight:900;
                margin-bottom:8px;
            ">
                ${escapeHTML(winner.name)}
            </div>

            <div style="font-size:20px;font-weight:700;">
                ${Number(winner.score)} PUNTOS
            </div>

            <div style="font-size:15px;margin-top:12px;">
                ¡Enhorabuena por vuestra victoria!
            </div>
        </div>
    `;

    const podium = document.createElement("div");

    podium.style.cssText = `
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        align-items:end;
        gap:12px;
        width:100%;
        max-width:950px;
        margin:25px auto 35px;
    `;

    const podiumOrder = [
        { team: ranking[1], position: 1 },
        { team: ranking[0], position: 0 },
        { team: ranking[2], position: 2 }
    ];

    podiumOrder.forEach(item => {

        const team = item.team;
        const position = item.position;

        if (!team) {
            podium.appendChild(document.createElement("div"));
            return;
        }

        const place = document.createElement("div");

        place.style.cssText = `
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:flex-end;
            min-width:0;
            text-align:center;
        `;

        const isWinner = position === 0;

        const avatar = document.createElement("div");

        avatar.textContent = team.avatar || "🎮";

        avatar.style.cssText = `
            display:flex;
            align-items:center;
            justify-content:center;
            width:${isWinner ? "clamp(75px,12vw,125px)" : "clamp(60px,9vw,95px)"};
            height:${isWinner ? "clamp(75px,12vw,125px)" : "clamp(60px,9vw,95px)"};
            border-radius:50%;
            background:${team.color || "#6C5CE7"};
            border:${isWinner ? "6px solid #F1C40F" : "4px solid #FFFFFF"};
            box-shadow:0 5px 18px rgba(0,0,0,0.20);
            font-size:${isWinner ? "clamp(38px,7vw,65px)" : "clamp(30px,5vw,48px)"};
            margin-bottom:12px;
        `;

        const medal = document.createElement("div");

        medal.textContent = medals[position];

        medal.style.cssText = `
            font-size:${isWinner ? "clamp(38px,6vw,58px)" : "clamp(30px,5vw,43px)"};
            margin-bottom:5px;
        `;

        const name = document.createElement("div");

        name.textContent = team.name;

        name.style.cssText = `
            font-size:${isWinner ? "clamp(17px,3vw,25px)" : "clamp(14px,2.5vw,20px)"};
            font-weight:900;
            overflow-wrap:anywhere;
            margin-bottom:6px;
            color:var(--text-primary,#222);
        `;

        const score = document.createElement("div");

        score.textContent = `${Number(team.score)} PTS`;

        score.style.cssText = `
            font-size:${isWinner ? "clamp(18px,3vw,25px)" : "clamp(15px,2.5vw,19px)"};
            font-weight:900;
            margin-bottom:12px;
            color:var(--text-primary,#222);
        `;

        const base = document.createElement("div");

        base.style.cssText = `
            width:100%;
            height:${podiumHeights[position]};
            max-height:190px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:14px 14px 0 0;
            background:${podiumColors[position]};
            color:white;
            font-size:clamp(28px,5vw,48px);
            font-weight:900;
            box-shadow:0 5px 15px rgba(0,0,0,0.15);
        `;

        base.textContent = `${position + 1}º`;

        place.appendChild(medal);
        place.appendChild(avatar);
        place.appendChild(name);
        place.appendChild(score);
        place.appendChild(base);

        podium.appendChild(place);
    });

    winnerContainer.appendChild(podium);

    if (ranking.length > 3) {

        const otherTitle = document.createElement("h3");

        otherTitle.textContent = "CLASIFICACIÓN DEL RESTO DE EQUIPOS";

        otherTitle.style.cssText = `
            text-align:center;
            margin:30px 0 15px;
            font-size:20px;
            font-weight:900;
        `;

        scoreboard.appendChild(otherTitle);

        ranking.slice(3).forEach((team, index) => {

            const row = document.createElement("div");

            row.className = "final-team-row";

            row.innerHTML = `
                <span class="final-position">${index + 4}º</span>
                <span>${escapeHTML(team.avatar || "🎮")}</span>
                <strong>${escapeHTML(team.name)}</strong>
                <span>${Number(team.score)} puntos</span>
            `;

            scoreboard.appendChild(row);
        });
    }

    finalPanel.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ==========================================
// INICIO
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    ensureSubmitButton();
});
