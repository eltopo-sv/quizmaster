
"use strict";

// ==========================================
// CONFIGURACIÓN
// ==========================================

const API_GAMES = "/api/games/";
const API_QUESTIONS = "/api/questions";

const gameSelect = document.getElementById("gameSelect");
const refreshBtn = document.getElementById("refreshBtn");
const questionsContainer = document.getElementById("questionsContainer");
const messageArea = document.getElementById("messageArea");

const totalQuestions = document.getElementById("totalQuestions");
const availableQuestions = document.getElementById("availableQuestions");
const allQuestionsBadge = document.getElementById("allQuestionsBadge");

const sectionTitle = document.getElementById("sectionTitle");
const sectionDescription = document.getElementById("sectionDescription");

// Elementos de generación IA
const questionsSection = document.querySelector(".questions-section");
const generateSection = document.getElementById("generateSection");

const documentFile = document.getElementById("documentFile");
const questionNumber = document.getElementById("questionNumber");
const questionDifficulty = document.getElementById("questionDifficulty");
const generateQuestionsBtn = document.getElementById("generateQuestionsBtn");
const generationMessage = document.getElementById("generationMessage");

let currentGameId = null;
let currentView = "dashboard";
let questionsData = [];


// ==========================================
// PETICIONES API
// ==========================================

async function apiRequest(url, options = {}) {

    const headers = {
        ...(options.headers || {})
    };

    // FormData establece automáticamente su propio Content-Type
    // con el boundary necesario para enviar archivos.
    if (
        options.body &&
        !(options.body instanceof FormData) &&
        !headers["Content-Type"]
    ) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    let data;

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        let errorMessage =
            data.detail || data.message || `Error HTTP ${response.status}`;

        if (Array.isArray(errorMessage)) {
            errorMessage = errorMessage
                .map(error => error.msg || JSON.stringify(error))
                .join(". ");
        }

        if (typeof errorMessage !== "string") {
            errorMessage = JSON.stringify(errorMessage);
        }

        throw new Error(errorMessage);
    }

    return data;
}


// ==========================================
// MENSAJES
// ==========================================

function showMessage(message, type = "success") {

    messageArea.innerHTML = "";

    const element = document.createElement("div");

    element.className = `message ${type}`;
    element.textContent = message;

    messageArea.appendChild(element);

    setTimeout(() => {
        if (element.parentNode === messageArea) {
            messageArea.removeChild(element);
        }
    }, 4500);
}


// ==========================================
// CARGAR JUEGOS
// ==========================================

async function loadGames() {

    try {

        const games = await apiRequest(API_GAMES);

        gameSelect.innerHTML = "";

        if (!games.length) {

            const option = document.createElement("option");

            option.value = "";
            option.textContent = "No hay juegos disponibles";

            gameSelect.appendChild(option);

            currentGameId = null;
            questionsData = [];

            updateStatistics();
            renderEmpty("Primero debes crear un juego.");

            return;
        }

        games.forEach(game => {

            const option = document.createElement("option");

            option.value = game.id;
            option.textContent = game.title;

            gameSelect.appendChild(option);

        });

        const previousGameExists = games.some(
            game => String(game.id) === String(currentGameId)
        );

        if (!previousGameExists) {
            currentGameId = games[0].id;
        }

        gameSelect.value = currentGameId;

        await loadQuestions();

    } catch (error) {

        renderEmpty("No se pudieron cargar los juegos.");
        showMessage(error.message, "error");

    }
}


// ==========================================
// CARGAR TODAS LAS PREGUNTAS
// ==========================================

async function loadQuestions() {

    if (!currentGameId) {
        return;
    }

    questionsContainer.innerHTML = `
        <div class="loading-state">
            Cargando preguntas...
        </div>
    `;

    try {

        const result = await apiRequest(
            `${API_QUESTIONS}/all/${currentGameId}`
        );

        questionsData = result.questions || [];

        updateStatistics();
        renderCurrentView();

    } catch (error) {

        renderEmpty("No se pudieron cargar las preguntas.");
        showMessage(error.message, "error");

    }
}


// ==========================================
// ESTADÍSTICAS
// ==========================================

function updateStatistics() {

    const total = questionsData.length;

    totalQuestions.textContent = total;
    availableQuestions.textContent = total;
    allQuestionsBadge.textContent = total;

}


// ==========================================
// CAMBIAR VISTA
// ==========================================

function setView(view) {

    currentView = view;

    document.querySelectorAll(".nav-item").forEach(button => {

        button.classList.toggle(
            "active",
            button.dataset.view === view
        );

    });

    renderCurrentView();

}


// ==========================================
// MOSTRAR VISTA ACTUAL
// ==========================================

function renderCurrentView() {

    // Mostrar generación IA
    if (currentView === "generate") {

        questionsSection.hidden = true;
        generateSection.hidden = false;

        return;
    }

    // Mostrar banco de preguntas
    questionsSection.hidden = false;
    generateSection.hidden = true;

    if (currentView === "dashboard") {

        sectionTitle.textContent = "Resumen de preguntas";

        sectionDescription.textContent =
            "Consulta y gestiona todas las preguntas de este juego.";

        renderDashboard();

        return;
    }

    if (currentView === "all") {

        sectionTitle.textContent = "Todas las preguntas";

        sectionDescription.textContent =
            "Puedes consultar y editar cualquier pregunta cuando lo necesites.";

        renderQuestions(questionsData);

    }

}


// ==========================================
// VISTA RESUMEN
// ==========================================

function renderDashboard() {

    const total = questionsData.length;

    questionsContainer.innerHTML = `
        <div class="dashboard-summary">
            <div class="summary-box">
                <strong>${total}</strong>
                <span>Preguntas disponibles para gestionar</span>
                <button class="action-button" data-action="all">
                    Consultar todas las preguntas
                </button>
            </div>
        </div>
    `;

}


// ==========================================
// MOSTRAR PREGUNTAS
// ==========================================

function renderQuestions(questions) {

    questionsContainer.innerHTML = "";

    if (!questions.length) {

        renderEmpty("Este juego todavía no tiene preguntas.");

        return;
    }

    questions.forEach(question => {

        const card = createQuestionCard(question);

        questionsContainer.appendChild(card);

    });

}


// ==========================================
// CREAR TARJETA
// ==========================================

function createQuestionCard(question) {

    const card = document.createElement("article");

    card.className = "question-card";

    const header = document.createElement("div");
    header.className = "question-header";

    const number = document.createElement("span");
    number.className = "question-number";
    number.textContent = `PREGUNTA #${question.id}`;

    const status = document.createElement("span");
    status.className = "question-status approved";
    status.textContent = "Disponible";

    header.append(number, status);

    const content = document.createElement("div");
    content.className = "question-content";

    const title = document.createElement("h3");
    title.textContent = question.text;

    content.appendChild(title);

    const options = document.createElement("div");
    options.className = "answer-options";

    ["A", "B", "C", "D"].forEach(letter => {

        const option = document.createElement("div");

        option.className =
            "answer-option" +
            (question.correct_option === letter ? " correct" : "");

        const label = document.createElement("strong");
        label.textContent = letter;

        const text = document.createElement("span");
        text.textContent =
            question[`option_${letter.toLowerCase()}`] || "";

        option.append(label, text);

        if (question.correct_option === letter) {

            const correct = document.createElement("small");

            correct.textContent = "✓ CORRECTA";

            option.appendChild(correct);

        }

        options.appendChild(option);

    });

    content.appendChild(options);

    const explanation = document.createElement("div");
    explanation.className = "question-explanation";

    const explanationTitle = document.createElement("strong");
    explanationTitle.textContent = "Explicación";

    const explanationText = document.createElement("p");

    explanationText.textContent =
        question.explanation || "Sin explicación.";

    explanation.append(explanationTitle, explanationText);

    content.appendChild(explanation);

    card.append(header, content);

    // Acciones
    const actions = document.createElement("div");
    actions.className = "question-actions";

    const editButton = document.createElement("button");

    editButton.className = "edit-button";
    editButton.textContent = "✎ Editar";

    editButton.addEventListener("click", () => {

        renderEditor(card, question);

    });

    actions.appendChild(editButton);
    card.appendChild(actions);

    return card;

}


// ==========================================
// EDITOR DE PREGUNTAS
// ==========================================

function renderEditor(card, question) {

    card.innerHTML = "";

    const form = document.createElement("form");

    form.className = "question-editor";

    function createField(labelText, value, name, multiline = false) {

        const wrapper = document.createElement("label");

        wrapper.className = "editor-field";

        const label = document.createElement("span");

        label.textContent = labelText;

        const input = multiline
            ? document.createElement("textarea")
            : document.createElement("input");

        input.name = name;
        input.value = value || "";
        input.required = name !== "explanation";

        wrapper.append(label, input);

        return wrapper;

    }

    form.appendChild(
        createField("Enunciado", question.text, "text", true)
    );

    ["A", "B", "C", "D"].forEach(letter => {

        form.appendChild(
            createField(
                `Respuesta ${letter}`,
                question[`option_${letter.toLowerCase()}`],
                `option_${letter.toLowerCase()}`
            )
        );

    });

    const correctWrapper = document.createElement("label");

    correctWrapper.className = "editor-field";

    const correctLabel = document.createElement("span");

    correctLabel.textContent = "Respuesta correcta";

    const correctSelect = document.createElement("select");

    correctSelect.name = "correct_option";
    correctSelect.required = true;

    ["A", "B", "C", "D"].forEach(letter => {

        const option = document.createElement("option");

        option.value = letter;
        option.textContent = `Respuesta ${letter}`;

        correctSelect.appendChild(option);

    });

    correctSelect.value = question.correct_option;

    correctWrapper.append(correctLabel, correctSelect);

    form.appendChild(correctWrapper);

    form.appendChild(
        createField(
            "Explicación",
            question.explanation,
            "explanation",
            true
        )
    );

    const buttons = document.createElement("div");

    buttons.className = "editor-actions";

    const saveButton = document.createElement("button");

    saveButton.type = "submit";
    saveButton.className = "approve-button";
    saveButton.textContent = "Guardar cambios";

    const cancelButton = document.createElement("button");

    cancelButton.type = "button";
    cancelButton.className = "cancel-button";
    cancelButton.textContent = "Cancelar";

    cancelButton.addEventListener("click", () => {

        renderCurrentView();

    });

    buttons.append(saveButton, cancelButton);

    form.appendChild(buttons);

    form.addEventListener("submit", async event => {

        event.preventDefault();

        const formData = new FormData(form);

        const data = Object.fromEntries(formData.entries());

        saveButton.disabled = true;
        saveButton.textContent = "Guardando...";

        try {

            await apiRequest(
                `${API_QUESTIONS}/${question.id}`,
                {
                    method: "PUT",
                    body: JSON.stringify(data)
                }
            );

            showMessage("Pregunta actualizada correctamente.");

            await loadQuestions();

        } catch (error) {

            showMessage(error.message, "error");

            saveButton.disabled = false;
            saveButton.textContent = "Guardar cambios";

        }

    });

    card.appendChild(form);

}


// ==========================================
// GENERAR PREGUNTAS CON IA
// ==========================================

async function generateQuestions() {

    // Comprobar juego
    if (!currentGameId) {

        generationMessage.textContent =
            "Primero debes seleccionar un juego.";

        return;
    }

    // Comprobar documento
    const file = documentFile.files[0];

    if (!file) {

        generationMessage.textContent =
            "Selecciona primero un documento PDF o DOCX.";

        return;
    }

    // Comprobar extensión
    const extension = file.name.split(".").pop().toLowerCase();

    if (!["pdf", "docx"].includes(extension)) {

        generationMessage.textContent =
            "El documento debe estar en formato PDF o DOCX.";

        return;
    }

    // Comprobar tamaño: 10 MB
    if (file.size > 10 * 1024 * 1024) {

        generationMessage.textContent =
            "El documento supera el límite de 10 MB.";

        return;
    }

    // Preparar datos
    const formData = new FormData();

    formData.append("game_id", currentGameId);
    formData.append("number", questionNumber.value);
    formData.append("difficulty", questionDifficulty.value);
    formData.append("file", file);

    // Estado de carga
    generateQuestionsBtn.disabled = true;

    generateQuestionsBtn.textContent =
        "⏳ Analizando documento y generando preguntas...";

    generationMessage.textContent =
        "La IA está trabajando. Este proceso puede tardar unos segundos.";

    try {

        const result = await apiRequest(
            `${API_QUESTIONS}/generate`,
            {
                method: "POST",
                body: formData
            }
        );

        const generatedCount =
            result.generated_count ??
            result.count ??
            (Array.isArray(result.questions)
                ? result.questions.length
                : 0);

        generationMessage.textContent =
            result.message ||
            `Generación completada. Se han creado ${generatedCount} preguntas.`;

        showMessage(
            `Se han generado ${generatedCount} preguntas correctamente.`
        );

        // Actualizar el banco y los contadores
        await loadQuestions();

        // Limpiar documento
        documentFile.value = "";

    } catch (error) {

        generationMessage.textContent =
            `No se pudieron generar las preguntas: ${error.message}`;

        showMessage(error.message, "error");

    } finally {

        generateQuestionsBtn.disabled = false;

        generateQuestionsBtn.textContent =
            "✦ Generar preguntas con IA";

    }

}


// ==========================================
// ESTADO VACÍO
// ==========================================

function renderEmpty(message) {

    questionsContainer.innerHTML = "";

    const element = document.createElement("div");

    element.className = "loading-state";
    element.textContent = message;

    questionsContainer.appendChild(element);

}


// ==========================================
// EVENTOS
// ==========================================

// Cambiar de juego
gameSelect.addEventListener("change", async () => {

    currentGameId = gameSelect.value;

    await loadQuestions();

});

// Actualizar preguntas
refreshBtn.addEventListener("click", loadQuestions);

// Navegación lateral
document.querySelectorAll(".nav-item").forEach(button => {

    button.addEventListener("click", () => {

        setView(button.dataset.view);

    });

});

// Botones internos del resumen
questionsContainer.addEventListener("click", event => {

    const button = event.target.closest("[data-action]");

    if (!button) {
        return;
    }

    setView(button.dataset.action);

});

// Generar preguntas
generateQuestionsBtn.addEventListener("click", generateQuestions);


// ==========================================
// INICIAR PANEL
// ==========================================

loadGames();
