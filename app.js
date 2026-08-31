// Constantes y Variables Globales
let SERVER_URL = window.location.origin;

let isListening = false;
let recognition = null;
let recentItems = [];
let historicoProductos = [];
let stockReferencia = [];
let ALIASES = {};
let categorias = [];

let lastSentTime = 0;
let lastSentPayload = "";

// --- DOM Elements ---
const micBtn = document.getElementById('mic-btn');
const micStatusText = document.getElementById('mic-status-text');
const liveText = document.getElementById('live-text');
const itemsList = document.getElementById('items-list');
const undoBtn = document.getElementById('undo-btn');
const downloadBtn = document.getElementById('download-btn');
const clearMonthBtn = document.getElementById('clear-month-btn');
const adminToggleBtn = document.getElementById('admin-toggle-btn');
const logoutBtn = document.getElementById('logout-btn');
const categoryDropdown = document.getElementById('category-dropdown');
const statusIndicator = document.getElementById('status-indicator');

const progressContainer = document.getElementById('progress-container');
const progressText = document.getElementById('progress-text');
const progressPercent = document.getElementById('progress-percent');
const progressBarFill = document.getElementById('progress-bar-fill');

const laboratorioToggleBtn = document.getElementById('laboratorio-toggle-btn');
const laboratorioView = document.getElementById('laboratorio-view');
const closeLaboratorioBtn = document.getElementById('close-laboratorio-btn');
const formRecetaContainer = document.getElementById('form-receta-container');
const formReceta = document.getElementById('form-receta');
const listaRecetas = document.getElementById('lista-recetas');

const toast = document.getElementById('toast');

const manualBtn = document.getElementById('manual-btn');
const manualForm = document.getElementById('manual-form');
const manualInput = document.getElementById('manual-input');

const loginView = document.getElementById('login-view');
const appView = document.getElementById('app-view');
const adminView = document.getElementById('admin-view');
const closeAdminBtn = document.getElementById('close-admin-btn');
const loginForm = document.getElementById('login-form');
const dniInput = document.getElementById('dni-input');
const passwordInput = document.getElementById('password-input');
const loginError = document.getElementById('login-error');
const userDisplay = document.getElementById('user-display');
const settingsBtnLogin = document.getElementById('settings-btn-login');

// --- Inicialización ---
async function init() {
    setupServerUrl();
    
    const storedUser = localStorage.getItem('usuario_lovo_nombre');
    const storedRol = localStorage.getItem('usuario_lovo_rol');
    
    // Si tiene usuario pero NO tiene rol (sesión antigua), forzar salir
    if (storedUser && (!storedRol || storedRol === 'undefined' || storedRol === 'null')) {
        handleLogout();
    } else if (storedUser) {
        showApp(storedUser, storedRol);
    } else {
        showLogin();
    }
    
    setupSpeechRecognition();
    setupAudioFeedback();
    
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    micBtn.addEventListener('click', toggleListening);
    undoBtn.addEventListener('click', undoLastItem);
    adminToggleBtn.addEventListener('click', toggleAdminView);
    closeAdminBtn.addEventListener('click', toggleAdminView);
    
    if(laboratorioToggleBtn) {
        laboratorioToggleBtn.addEventListener('click', toggleLaboratorioView);
    }
    if(closeLaboratorioBtn) {
        closeLaboratorioBtn.addEventListener('click', toggleLaboratorioView);
    }
    if(formReceta) {
        formReceta.addEventListener('submit', handleCrearReceta);
    }
    
    if(categoryDropdown) {
        categoryDropdown.addEventListener('change', (e) => {
            localStorage.setItem('last_category', e.target.value);
            renderList();
        });
    }
    if(downloadBtn) {
        downloadBtn.addEventListener('click', downloadExcel);
    }
    if(clearMonthBtn) {
        clearMonthBtn.addEventListener('click', clearMonthInventory);
    }
    if(settingsBtnLogin) {
        settingsBtnLogin.addEventListener('click', forceSetupServerUrl);
    }
    if(manualBtn) {
        manualBtn.addEventListener('click', () => {
            if(manualForm.classList.contains('hidden')) {
                manualForm.classList.remove('hidden');
                manualForm.style.display = 'flex';
                manualInput.focus();
            } else {
                manualForm.classList.add('hidden');
                manualForm.style.display = 'none';
            }
        });
    }
    if(manualForm) {
        manualForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = manualInput.value;
            if(text.trim()) {
                liveText.textContent = "Procesando manual: " + text;
                processVoiceCommand(text);
                manualInput.value = '';
                manualForm.classList.add('hidden');
                manualForm.style.display = 'none';
            }
        });
    }
    const searchInput = document.getElementById('search-input');
    if(searchInput) {
        searchInput.addEventListener('input', () => {
            renderList(searchInput.value.toLowerCase());
        });
    }
    
    setupAdminTabs();
}

function showLogin() {
    loginView.classList.remove('hidden');
    loginView.classList.add('active');
    appView.classList.remove('active');
    appView.classList.add('hidden');
    adminView.classList.add('hidden');
}

function handleLogout() {
    localStorage.removeItem('usuario_lovo_nombre');
    localStorage.removeItem('usuario_lovo_dni');
    localStorage.removeItem('usuario_lovo_rol');
    localStorage.removeItem('usuario_lovo_token');
    showLogin();
}

function showApp(userName, userRol) {
    loginView.classList.remove('active');
    loginView.classList.add('hidden');
    appView.classList.remove('hidden');
    appView.classList.add('active');
    adminView.classList.add('hidden');
    if(laboratorioView) laboratorioView.classList.add('hidden');
    
    let rolText = ' (Camarero)';
    if(userRol === 'encargado') rolText = ' (Encargado)';
    if(userRol === 'produccion') rolText = ' (Producción)';
    userDisplay.textContent = userName + rolText;
    
    if(userRol === 'encargado') {
        adminToggleBtn.classList.remove('hidden');
        downloadBtn.classList.remove('hidden');
        clearMonthBtn.classList.remove('hidden');
    } else {
        adminToggleBtn.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        clearMonthBtn.classList.add('hidden');
    }
    
    if(userRol === 'encargado' || userRol === 'produccion') {
        if(laboratorioToggleBtn) laboratorioToggleBtn.classList.remove('hidden');
    } else {
        if(laboratorioToggleBtn) laboratorioToggleBtn.classList.add('hidden');
    }
    
    checkServerConnection();
    fetchStockReferencia();
}

async function handleLogin(e) {
    e.preventDefault();
    loginError.classList.add('hidden');
    
    const dni = dniInput.value.trim();
    const password = passwordInput.value;
    
    if (!dni || !password) return;
    
    try {
        const response = await fetch(`${SERVER_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dni, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('usuario_lovo_dni', dni);
            localStorage.setItem('usuario_lovo_nombre', data.nombre);
            localStorage.setItem('usuario_lovo_rol', data.rol);
            localStorage.setItem('usuario_lovo_token', data.token);
            showApp(data.nombre, data.rol);
        } else {
            loginError.textContent = "Credenciales incorrectas";
            loginError.classList.remove('hidden');
        }
    } catch (error) {
        loginError.textContent = "Error al conectar con el servidor";
        loginError.classList.remove('hidden');
    }
}

function forceSetupServerUrl() {
    const ip = prompt("Si usas una IP local separada, indícala (Ej: http://192.168.1.50:8000). Si no, déjalo en blanco para usar la URL actual:");
    if (ip) {
        SERVER_URL = ip.startsWith('http') ? ip : `http://${ip}`;
        localStorage.setItem('server_url', SERVER_URL);
    } else {
        SERVER_URL = window.location.origin;
        localStorage.removeItem('server_url');
    }
    checkServerConnection();
}

function setupServerUrl() {
    const savedUrl = localStorage.getItem('server_url');
    if (savedUrl) {
        SERVER_URL = savedUrl;
    } else {
        SERVER_URL = window.location.origin;
    }
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('usuario_lovo_token')}`
    };
}

async function checkServerConnection() {
    try {
        await fetch(`${SERVER_URL}/api/productos`, { headers: getAuthHeaders() }); 
        updateStatus(true);
        await Promise.all([
            fetchCategorias(),
            fetchDiccionario(),
            fetchInventarioHoy(),
            fetchProductosHistoricos()
        ]);
    } catch (e) {
        updateStatus(false);
    }
}

// --- Data Fetching ---
async function fetchCategorias() {
    try {
        const response = await fetch(`${SERVER_URL}/api/admin/categorias`, { headers: getAuthHeaders() });
        if(response.ok) {
            const data = await response.json();
            categorias = data.map(c => c.nombre);
            renderCategorias();
        }
    } catch(e) { console.error("Error cargando categorias", e); }
}

async function fetchDiccionario() {
    try {
        const response = await fetch(`${SERVER_URL}/api/admin/diccionario`, { headers: getAuthHeaders() });
        if(response.ok) {
            const data = await response.json();
            ALIASES = {};
            data.forEach(d => { ALIASES[d.alias] = d.real_name; });
        }
    } catch(e) { console.error("Error cargando diccionario", e); }
}

function renderCategorias() {
    categoryDropdown.innerHTML = '';
    categorias.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = cat;
        categoryDropdown.appendChild(option);
    });
    const lastCat = localStorage.getItem('last_category');
    if(lastCat && categorias.includes(lastCat)) {
        categoryDropdown.value = lastCat;
    }
}

// --- Audio & Speech (omitted logic unchanged mostly, but rewritten for brevity/completeness) ---
let beepAudio;
function setupAudioFeedback() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
        const audioCtx = new AudioContext();
        
        // iOS Safari requiere desbloquear el audio con una interacción directa
        const unlockAudio = () => {
            if(audioCtx.state === 'suspended') audioCtx.resume();
            document.removeEventListener('click', unlockAudio);
            document.removeEventListener('touchstart', unlockAudio);
        };
        document.addEventListener('click', unlockAudio);
        document.addEventListener('touchstart', unlockAudio);

        beepAudio = function() {
            if(audioCtx.state === 'suspended') audioCtx.resume();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
            gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.05);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            oscillator.start(audioCtx.currentTime);
            oscillator.stop(audioCtx.currentTime + 0.2);
        };
    } else {
        beepAudio = () => { console.log('Beep no soportado'); };
    }
}

let speechTimeout = null;
let currentTranscript = "";

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false; // CLAVE: en false, Android procesa la frase entera y se detiene
    recognition.interimResults = true;
    
    recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        micStatusText.textContent = "Escuchando...";
        micStatusText.style.color = "#ef4444";
        liveText.classList.remove('placeholder');
    };
    
    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        
        currentTranscript = transcript;
        liveText.textContent = currentTranscript;
        
        // Si el navegador ya detectó que es el final de la frase (isFinal = true)
        if (event.results[0] && event.results[0].isFinal) {
            clearTimeout(speechTimeout);
            const finalText = currentTranscript.trim().toLowerCase();
            currentTranscript = "";
            
            if (finalText) {
                liveText.textContent = "Procesando: " + finalText;
                processVoiceCommand(finalText);
            }
        }
    };
    
    recognition.onend = () => {
        // Como pusimos continuous=false, se detendrá solo. Aquí lo volvemos a encender.
        if (isListening) {
            try { recognition.start(); } catch(e) { stopListening(); }
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
            stopListening();
            showToast("Error: Permiso de micrófono denegado.");
        }
    };
}

function toggleListening() { isListening ? stopListening() : startListening(); }
function startListening() { if (recognition) { try { recognition.start(); } catch(e){} } }
function stopListening() {
    isListening = false;
    if (recognition) recognition.stop();
    micBtn.classList.remove('listening');
    micStatusText.textContent = "Toca para hablar";
    micStatusText.style.color = "";
    liveText.textContent = "Micrófono detenido...";
    liveText.classList.add('placeholder');
}

const NUMEROS_ES = {
    'cero': 0, 'un': 1, 'una': 1, 'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 
    'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
    'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15, 
    'dieciseis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19,
    'veinte': 20, 'veintiun': 21, 'veintiuno': 21, 'veintidos': 22, 'veintitres': 23,
    'veinticuatro': 24, 'veinticinco': 25, 'veintiseis': 26, 'veintisiete': 27,
    'veintiocho': 28, 'veintinueve': 29, 'treinta': 30, 'cuarenta': 40, 
    'cincuenta': 50, 'sesenta': 60, 'setenta': 70, 'ochenta': 80, 'noventa': 90, 'cien': 100
};

function normalizeText(text) {
    let t = text.toLowerCase();
    
    // Reemplaza comas literales entre números (ej. Android formatea "2,3" o "2 , 3" nativamente)
    t = t.replace(/(\d)\s*,\s*(\d)/g, '$1.$2');
    
    // Reemplaza palabras usadas como decimal
    t = t.replace(/\b(punto|coma|con)\b/g, '.');
    t = t.replace(/\by\s+medi[oa]\b/g, '.5');
    
    // Reemplaza compuestos como "treinta y cinco" -> 35
    t = t.replace(/\b(treinta|cuarenta|cincuenta|sesenta|setenta|ochenta|noventa)\s+y\s+(un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b/g, (match, decena, unidad) => {
        return (NUMEROS_ES[decena] + NUMEROS_ES[unidad]).toString();
    });
    
    // Reemplaza palabras sueltas de mayor a menor longitud
    const palabras = Object.keys(NUMEROS_ES).sort((a,b) => b.length - a.length);
    for (const word of palabras) {
        t = t.replace(new RegExp(`\\b${word}\\b`, 'g'), NUMEROS_ES[word]);
    }
    
    // Une los números con el punto decimal tolerando espacios (ej. "2 . 3" o "2 .5" o "2. 5" -> "2.5")
    t = t.replace(/(\d)\s*\.\s*(\d)/g, '$1.$2');
    
    return t;
}

function applyAlias(producto) {
    let p = producto;
    for (const [alias, realName] of Object.entries(ALIASES)) {
        if (p.includes(alias)) p = p.replace(alias, realName);
    }
    return p.charAt(0).toUpperCase() + p.slice(1);
}

function levenshteinDistance(a, b) {
    const matrix = [];
    for (let i = 0; i <= b.length; i++) matrix[i] = [i];
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
            }
        }
    }
    return matrix[b.length][a.length];
}

function findClosestMatch(producto) {
    if (historicoProductos.length === 0) return producto;
    let bestMatch = producto;
    let minDistance = Infinity;
    
    // Umbral dinámico: permite hasta un 30% de error en la frase (mínimo 2 letras)
    // Así corrige "cajas de pecho" (error de 3 letras en 14 = 21%) a "cajas de pepsi"
    const threshold = Math.max(2, Math.floor(producto.length * 0.3));
    
    // Si el producto dictado contiene números (ej: 1.5), NO hacemos autocorrección para no destruir el tamaño
    if (/\d/.test(producto)) return producto;
    
    const lowerProducto = producto.toLowerCase();
    for (const hist of historicoProductos) {
        const dist = levenshteinDistance(lowerProducto, hist.toLowerCase());
        if (dist < minDistance) {
            minDistance = dist;
            bestMatch = hist;
        }
    }
    return (minDistance <= threshold) ? bestMatch : producto;
}

function processVoiceCommand(command) {
    const normalized = normalizeText(command);
    if (!normalized || normalized.trim() === '') return;
    
    const activeCategory = categoryDropdown.value;
    
    // Buscar la cantidad (entero o decimal) SIEMPRE al principio
    const regex = /^(\d+(?:\.\d+)?)\s+(.+)$/;
    const match = normalized.match(regex);
    
    if (match) {
        const cantidad = parseFloat(match[1]);
        const productoRaw = match[2].trim();
        let producto = applyAlias(productoRaw);
        const matchedProducto = findClosestMatch(producto);
        sendToServer(activeCategory, matchedProducto, cantidad, producto !== matchedProducto);
        return;
    }
    // Si no detectamos ningún número, lo ignoramos para evitar que grabe ruido o frases a medias
    showToast("⚠️ Debe decir el número. Ej: 'Dos Coca Colas'");
}

async function fetchInventarioHoy() {
    try {
        const response = await fetch(`${SERVER_URL}/api/inventario/hoy`, { headers: getAuthHeaders() });
        if (response.ok) {
            const data = await response.json();
            recentItems = data.registros || [];
            renderList();
            updateProgressBar();
        }
    } catch (error) {}
}

async function fetchStockReferencia() {
    try {
        const response = await fetch(`${SERVER_URL}/api/inventario/referencia`, { headers: getAuthHeaders() });
        if (response.ok) {
            const data = await response.json();
            stockReferencia = data.referencia || [];
            updateProgressBar();
        }
    } catch (error) {}
}

function updateProgressBar() {
    if (stockReferencia.length === 0) {
        progressContainer.style.display = 'none';
        return;
    }
    progressContainer.style.display = 'block';
    
    const dictadosSet = new Set(recentItems.map(i => i.producto.toLowerCase()));
    
    let counted = 0;
    let total = stockReferencia.length;
    
    for (let ref of stockReferencia) {
        if (dictadosSet.has(ref.producto.toLowerCase())) {
            counted++;
        }
    }
    
    let percent = total === 0 ? 0 : Math.round((counted / total) * 100);
    progressText.textContent = `${counted} de ${total} referencias activas completadas`;
    progressPercent.textContent = `${percent}%`;
    progressBarFill.style.width = `${percent}%`;
}

async function fetchProductosHistoricos() {
    try {
        const response = await fetch(`${SERVER_URL}/api/productos`, { headers: getAuthHeaders() });
        if (response.ok) {
            const data = await response.json();
            historicoProductos = data.productos || [];
        }
    } catch (error) {}
}

async function downloadExcel() {
    try {
        const response = await fetch(`${SERVER_URL}/api/descargar/hoy`, { headers: getAuthHeaders() });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Inventario_Hoy.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert('Error descargando Excel');
        }
    } catch (e) {
        console.error(e);
    }
}


async function sendToServer(categoria, producto, cantidad, fueCorregido = false) {
    const payloadStr = `${categoria}|${producto}|${cantidad}`;
    const now = Date.now();
    if (payloadStr === lastSentPayload && (now - lastSentTime) < 4000) return;
    lastSentPayload = payloadStr;
    lastSentTime = now;
    
    liveText.textContent = `Guardando: ${cantidad} de ${producto}...`;
    const payload = { categoria: categoria, producto: producto, cantidad_dictada: cantidad, usuario: localStorage.getItem('usuario_lovo_nombre') || "Desconocido" };

    try {
        const response = await fetch(`${SERVER_URL}/api/registro`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(payload)
        });
        if (response.ok) {
            if(beepAudio) beepAudio();
            showToast();
            fetchInventarioHoy();
            updateStatus(true);
            liveText.textContent = fueCorregido ? `¡Registrado y Corregido a! ${cantidad} ${producto}` : `¡Registrado! ${cantidad} ${producto}`;
            if (!historicoProductos.includes(producto)) historicoProductos.push(producto);
            setTimeout(() => { if(isListening) liveText.textContent = "Escuchando..."; }, 2500);
        } else throw new Error("Error en respuesta");
    } catch (error) {
        liveText.textContent = "Error al guardar. Revisa conexión.";
        updateStatus(false);
    }
}

async function undoLastItem() {
    if (recentItems.length === 0) return;
    try {
        const response = await fetch(`${SERVER_URL}/api/registro/ultimo`, { method: 'DELETE', headers: getAuthHeaders() });
        if (response.ok) {
            const data = await response.json();
            if (data.status === "warning") {
                showToast(data.message);
            } else {
                fetchInventarioHoy();
                showToast("Registro borrado");
            }
        }
    } catch (error) {}
}

async function clearMonthInventory() {
    if (confirm("⚠️ ¿ESTÁS SEGURO?\n\nEsto borrará TODO el inventario de la base de datos para empezar un nuevo mes.\n\n¡Asegúrate de haber descargado el Excel antes!")) {
        try {
            const response = await fetch(`${SERVER_URL}/api/inventario/todo`, { method: 'DELETE', headers: getAuthHeaders() });
            if (response.ok) {
                fetchInventarioHoy();
                historicoProductos = [];
                alert("Inventario borrado por completo.");
            }
        } catch (error) {}
    }
}

function renderList(filterText = '') {
    itemsList.innerHTML = '';
    
    if (recentItems.length === 0) {
        itemsList.innerHTML = `<li class="item-card" style="justify-content: center; color: var(--text-muted); font-style: italic;">Sin registros hoy</li>`;
        undoBtn.disabled = true;
        return;
    }
    
    undoBtn.disabled = false;
    
    // Group by category, but keep order within category
    const grupos = {};
    recentItems.forEach(item => {
        if (!grupos[item.categoria]) grupos[item.categoria] = [];
        // Filtering
        if (filterText) {
            if (item.producto.toLowerCase().includes(filterText)) {
                grupos[item.categoria].push(item);
            }
        } else {
            grupos[item.categoria].push(item);
        }
    });
    
    // Determine the category to auto-expand (usually the one from the most recent item, i.e., index 0)
    let autoExpandCategory = null;
    if (!filterText && recentItems.length > 0) {
        autoExpandCategory = recentItems[0].categoria;
    }
    
    for (const [categoria, items] of Object.entries(grupos)) {
        if (items.length === 0) continue; // Skip empty categories after filter

        // Create accordion header
        const header = document.createElement('div');
        header.className = 'category-header';
        const isExpanded = (categoria === autoExpandCategory) || (filterText.length > 0);
        if (isExpanded) header.classList.add('active');
        
        header.innerHTML = `
            <span>${categoria} <span style="color:var(--text-muted); font-size:0.7rem; margin-left:5px;">(${items.length})</span></span>
            <span class="chevron">▼</span>
        `;
        
        // Create accordion content
        const contentContainer = document.createElement('div');
        contentContainer.className = 'category-content';
        if (isExpanded) contentContainer.classList.add('active');
        
        // Toggle logic
        header.addEventListener('click', () => {
            header.classList.toggle('active');
            contentContainer.classList.toggle('active');
        });
        
        // Render items inside content (Limit visually to 50 to prevent lag)
        const renderLimit = 50;
        const itemsToRender = items.slice(0, renderLimit);
        
        itemsToRender.forEach(item => {
            const li = document.createElement('div');
            li.className = 'item-card-compact';
            
            const ref = stockReferencia.find(r => r.producto.toLowerCase() === item.producto.toLowerCase());
            let refBadge = '';
            if (ref) {
                refBadge = `<div style="font-size: 0.7rem; color: rgba(255,255,255,0.4); margin-top: 2px;">Stock previo: ${ref.stock_anterior} btls</div>`;
            }
            
            li.innerHTML = `
                <div class="item-info">
                    <span class="item-name">${item.producto}</span>
                    <span class="item-time">${item.hora}</span>
                    ${refBadge}
                </div>
                <div class="item-quantity">${item.cantidad_dictada}</div>
            `;
            contentContainer.appendChild(li);
        });
        
        if (items.length > renderLimit) {
            const moreMsg = document.createElement('div');
            moreMsg.style.cssText = "font-size: 0.75rem; color: var(--text-muted); text-align: center; padding: 5px; font-style: italic;";
            moreMsg.textContent = `...y ${items.length - renderLimit} más (descarga el Excel para ver todos)`;
            contentContainer.appendChild(moreMsg);
        }
        
        const wrapper = document.createElement('li');
        wrapper.style.listStyle = 'none';
        wrapper.appendChild(header);
        wrapper.appendChild(contentContainer);
        itemsList.appendChild(wrapper);
    }
}

function showToast(msg = "Registro guardado") {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => { toast.classList.remove('show'); }, 2500);
}

function updateStatus(isOnline) {
    if (isOnline) {
        statusIndicator.className = 'status-indicator online';
        statusIndicator.querySelector('.text').textContent = 'Conectado';
    } else {
        statusIndicator.className = 'status-indicator offline';
        statusIndicator.querySelector('.text').textContent = 'Desconectado';
    }
}

// --- ADMIN PANEL LOGIC ---
function toggleAdminView() {
    if(adminView.classList.contains('hidden')) {
        adminView.classList.remove('hidden');
        appView.classList.add('hidden');
        if(laboratorioView) laboratorioView.classList.add('hidden');
        loadAdminData();
    } else {
        adminView.classList.add('hidden');
        appView.classList.remove('hidden');
        checkServerConnection(); // Reload user side data (cats, dictionary)
    }
}

// --- LABORATORIO LOGIC ---
function toggleLaboratorioView() {
    if(laboratorioView.classList.contains('hidden')) {
        laboratorioView.classList.remove('hidden');
        appView.classList.add('hidden');
        adminView.classList.add('hidden');
        loadRecetas();
        
        if (localStorage.getItem('usuario_lovo_rol') === 'encargado') {
            formRecetaContainer.classList.remove('hidden');
        } else {
            formRecetaContainer.classList.add('hidden');
        }
    } else {
        laboratorioView.classList.add('hidden');
        appView.classList.remove('hidden');
        checkServerConnection();
    }
}

async function loadRecetas() {
    try {
        const res = await fetch(`${SERVER_URL}/api/recetas`, { headers: getAuthHeaders() });
        const data = await res.json();
        listaRecetas.innerHTML = '';
        const userRol = localStorage.getItem('usuario_lovo_rol');
        
        data.forEach(r => {
            const card = document.createElement('div');
            card.className = 'recipe-card';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:var(--primary-color);">${r.nombre}</h3>
                    <span style="font-size:0.8rem; background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px;">${r.categoria}</span>
                </div>
                <div style="margin-top:10px;">
                    <strong>Ingredientes:</strong><br>
                    <div style="white-space: pre-wrap; font-size:0.9rem; color:var(--text-main); margin-bottom:10px;">${r.ingredientes}</div>
                    <strong>Procedimiento:</strong><br>
                    <div style="white-space: pre-wrap; font-size:0.9rem; color:var(--text-main);">${r.procedimiento}</div>
                    ${userRol === 'encargado' ? `<div style="margin-top:10px; color:#10b981;"><strong>Coste Total:</strong> ${r.coste}</div>` : ''}
                </div>
                <div style="display:flex; gap:10px; margin-top:15px;">
                    <button class="download-btn" onclick="producirLote(${r.id})" style="flex:1;">✅ Registrar Lote Producido</button>
                    ${userRol === 'encargado' ? `<button class="btn-delete" onclick="borrarReceta(${r.id})">Borrar</button>` : ''}
                </div>
            `;
            listaRecetas.appendChild(card);
        });
    } catch(e) { console.error("Error cargando recetas", e); }
}

async function handleCrearReceta(e) {
    e.preventDefault();
    try {
        await fetch(`${SERVER_URL}/api/recetas`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({
                nombre: document.getElementById('new-receta-nombre').value,
                categoria: document.getElementById('new-receta-categoria').value,
                ingredientes: document.getElementById('new-receta-ingredientes').value,
                procedimiento: document.getElementById('new-receta-procedimiento').value,
                coste: document.getElementById('new-receta-coste').value
            })
        });
        e.target.reset();
        loadRecetas();
    } catch(err) { alert('Error creando receta'); }
}

async function borrarReceta(id) {
    if(confirm('¿Borrar esta ficha técnica?')) {
        await fetch(`${SERVER_URL}/api/recetas/${id}`, {method: 'DELETE', headers: getAuthHeaders()});
        loadRecetas();
    }
}

async function producirLote(id) {
    if(confirm('¿Registrar 1 lote/botella producida en el inventario?')) {
        try {
            const res = await fetch(`${SERVER_URL}/api/recetas/${id}/producir`, {method: 'POST', headers: getAuthHeaders()});
            if(res.ok) {
                showToast("¡Lote registrado en el inventario!");
            } else {
                alert('Error registrando lote');
            }
        } catch(e) { alert('Error de conexión'); }
    }
}

function setupAdminTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.add('hidden'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.remove('hidden');
        });
    });
    
    document.getElementById('form-usuario').addEventListener('submit', async (e) => {
        e.preventDefault();
        await fetch(`${SERVER_URL}/api/admin/usuarios`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({
                dni: document.getElementById('new-user-dni').value,
                nombre: document.getElementById('new-user-nombre').value,
                password: document.getElementById('new-user-pass').value,
                rol: document.getElementById('new-user-rol').value
            })
        });
        e.target.reset();
        loadAdminUsuarios();
    });
    
    document.getElementById('form-categoria').addEventListener('submit', async (e) => {
        e.preventDefault();
        await fetch(`${SERVER_URL}/api/admin/categorias`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({ nombre: document.getElementById('new-cat-nombre').value })
        });
        e.target.reset();
        loadAdminCategorias();
    });
    
    document.getElementById('form-diccionario').addEventListener('submit', async (e) => {
        e.preventDefault();
        await fetch(`${SERVER_URL}/api/admin/diccionario`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({
                alias: document.getElementById('new-dict-alias').value,
                real_name: document.getElementById('new-dict-real').value
            })
        });
        e.target.reset();
        loadAdminDiccionario();
    });
    
    const historyDateSelect = document.getElementById('history-date-select');
    if (historyDateSelect) {
        historyDateSelect.addEventListener('change', (e) => {
            if(e.target.value) {
                loadHistorialPorFecha(e.target.value);
            } else {
                document.getElementById('history-table-body').innerHTML = '';
            }
        });
    }
    
    const deleteHistoryBtn = document.getElementById('delete-history-btn');
    if (deleteHistoryBtn) {
        deleteHistoryBtn.addEventListener('click', async () => {
            const fecha = document.getElementById('history-date-select').value;
            if(!fecha) return alert("Selecciona una fecha primero");
            if(confirm(`¿Estás seguro de que deseas eliminar TODOS los registros de la fecha ${fecha}?`)) {
                try {
                    const res = await fetch(`${SERVER_URL}/api/inventario/historial?fecha=${encodeURIComponent(fecha)}`, {
                        method: 'DELETE',
                        headers: getAuthHeaders()
                    });
                    if(res.ok) {
                        alert("Fecha eliminada correctamente.");
                        loadHistorialFechas();
                        document.getElementById('history-cards-container').innerHTML = '';
                    } else {
                        alert("Error al eliminar la fecha.");
                    }
                } catch(e) { console.error(e); }
            }
        });
    }

    const downloadHistoryBtn = document.getElementById('download-history-btn');
    if (downloadHistoryBtn) {
        downloadHistoryBtn.addEventListener('click', async () => {
            const fecha = document.getElementById('history-date-select').value;
            if(!fecha) return alert("Selecciona una fecha primero");
            try {
                const response = await fetch(`${SERVER_URL}/api/descargar/hoy?fecha=${encodeURIComponent(fecha)}`, { headers: getAuthHeaders() });
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Inventario_${fecha.replace(/\//g, '-')}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                } else {
                    alert('Error descargando Excel del historial');
                }
    } catch (e) { console.error(e); }
        });
    }
    
    const balanceDateSelect = document.getElementById('balance-date-select');
    if (balanceDateSelect) {
        balanceDateSelect.addEventListener('change', (e) => {
            if(e.target.value) {
                loadBalancePorFecha(e.target.value);
            } else {
                document.getElementById('balance-table-body').innerHTML = '';
                document.getElementById('balance-total-cost').textContent = '0.00 €';
            }
        });
    }
    
    const historySearchInput = document.getElementById('history-search-input');
    if (historySearchInput) {
        historySearchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const accordions = document.querySelectorAll('.accordion');
            accordions.forEach(acc => {
                const cards = acc.querySelectorAll('.history-card');
                let hasMatch = false;
                cards.forEach(card => {
                    if(card.dataset.prod.includes(term)) {
                        card.style.display = 'grid';
                        hasMatch = true;
                    } else {
                        card.style.display = 'none';
                    }
                });
                if(hasMatch) {
                    acc.style.display = 'block';
                    if(term.length > 0) acc.querySelector('.accordion-content').classList.add('open');
                } else {
                    acc.style.display = 'none';
                }
            });
        });
    }
    
    const balanceSearchInput = document.getElementById('balance-search-input');
    if (balanceSearchInput) {
        balanceSearchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#balance-table-body tr');
            rows.forEach(row => {
                const prod = row.children[1].textContent.toLowerCase();
                if(prod.includes(term)) row.style.display = '';
                else row.style.display = 'none';
            });
        });
    }
    
    const formImportarExcel = document.getElementById('form-importar-excel');
    if (formImportarExcel) {
        formImportarExcel.addEventListener('submit', async (e) => {
            e.preventDefault();
            const dateInput = document.getElementById('import-excel-date').value;
            const fileInput = document.getElementById('import-excel-file').files[0];
            
            if(!dateInput || !fileInput) return alert('Por favor, rellena fecha y selecciona un archivo.');
            
            const formData = new FormData();
            formData.append('fecha', dateInput);
            formData.append('file', fileInput);
            
            const btn = e.target.querySelector('button');
            const originalText = btn.textContent;
            btn.textContent = 'Subiendo...';
            btn.disabled = true;
            
            try {
                const res = await fetch(`${SERVER_URL}/api/inventario/importar-excel`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('usuario_lovo_token')}` },
                    body: formData
                });
                
                const data = await res.json();
                if(res.ok) {
                    showToast('Excel subido y guardado exitosamente');
                    e.target.reset();
                    loadHistorialFechas();
                } else {
                    alert(data.detail || 'Error subiendo Excel');
                }
            } catch (err) {
                console.error(err);
                alert('Error de conexión');
            } finally {
                btn.textContent = originalText;
                btn.disabled = false;
            }
        });
    }
}

function loadAdminData() {
    loadAdminUsuarios();
    loadAdminCategorias();
    loadAdminDiccionario();
    loadHistorialFechas();
}

async function loadHistorialFechas() {
    try {
        const res = await fetch(`${SERVER_URL}/api/inventario/fechas`, { headers: getAuthHeaders() });
        const data = await res.json();
        
        const selectHist = document.getElementById('history-date-select');
        const selectBal = document.getElementById('balance-date-select');
        
        if (selectHist) {
            selectHist.innerHTML = '<option value="">Selecciona fecha</option>';
            data.fechas.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                selectHist.appendChild(opt);
            });
        }
        
        if (selectBal) {
            selectBal.innerHTML = '<option value="">Selecciona fecha</option>';
            data.fechas.forEach(f => {
                const opt = document.createElement('option');
                opt.value = f;
                opt.textContent = f;
                selectBal.appendChild(opt);
            });
        }
    } catch(e) { console.error("Error cargando fechas de historial", e); }
}

async function loadBalancePorFecha(fecha) {
    try {
        const res = await fetch(`${SERVER_URL}/api/inventario/comparativa?fecha=${encodeURIComponent(fecha)}`, { headers: getAuthHeaders() });
        const data = await res.json();
        const tbody = document.getElementById('balance-table-body');
        if (!tbody) return;
        tbody.innerHTML = '';
        
        let costeTotal = 0;
        
        data.comparativa.forEach(c => {
            const tr = document.createElement('tr');
            
            let badge = '';
            if (c.alerta === 'OK') badge = '<span style="color:#10b981;">🟢 OK</span>';
            else if (c.alerta === 'No Contado') badge = '<span style="color:#f59e0b;">🟠 No Contado</span>';
            else if (c.alerta === 'Stock Negativo') badge = '<span style="color:#ef4444;">🔴 Negativo</span>';
            else if (c.alerta === 'Consumo Elevado') badge = '<span style="color:#ef4444;">🔴 Elevado</span>';
            
            tr.innerHTML = `
                <td>${badge}</td>
                <td style="font-weight:bold;">${c.producto}</td>
                <td><span style="font-size:0.75rem; color:var(--primary-color);">${c.categoria}</span></td>
                <td style="text-align:center;">${c.stock_anterior}</td>
                <td style="text-align:center;">${c.stock_actual}</td>
                <td style="text-align:center; font-weight:bold;">${c.consumo}</td>
                <td style="text-align:right;">${c.coste_consumo.toFixed(2)} €</td>
            `;
            tbody.appendChild(tr);
            
            costeTotal += c.coste_consumo;
        });
        
        document.getElementById('balance-total-cost').textContent = costeTotal.toFixed(2) + ' €';
        
    } catch(e) { console.error("Error cargando comparativa", e); }
}

async function loadHistorialPorFecha(fecha) {
    try {
        const res = await fetch(`${SERVER_URL}/api/inventario/historial?fecha=${encodeURIComponent(fecha)}`, { headers: getAuthHeaders() });
        const data = await res.json();
        const container = document.getElementById('history-cards-container');
        if (!container) return;
        container.innerHTML = '';
        
        const categorias = {};
        data.registros.forEach(r => {
            if(!categorias[r.categoria]) categorias[r.categoria] = [];
            categorias[r.categoria].push(r);
        });
        
        for (const cat in categorias) {
            const acc = document.createElement('div');
            acc.className = 'accordion';
            
            const header = document.createElement('div');
            header.className = 'accordion-header';
            header.innerHTML = `<span>${cat}</span> <span style="font-size:0.8rem; opacity:0.8;">${categorias[cat].length} ítems ▾</span>`;
            
            const content = document.createElement('div');
            content.className = 'accordion-content';
            
            categorias[cat].forEach(r => {
                const card = document.createElement('div');
                card.className = 'history-card';
                card.dataset.prod = r.producto.toLowerCase();
                card.innerHTML = `
                    <div class="prod-name">${r.producto}</div>
                    <div class="prod-data"><strong>${r.botellas_llenas}</strong> btls</div>
                    <div class="prod-data">${r.restante_porcentaje}</div>
                    <div class="prod-user">${r.usuario}</div>
                `;
                content.appendChild(card);
            });
            
            header.onclick = () => {
                content.classList.toggle('open');
                const isOp = content.classList.contains('open');
                header.querySelector('span:last-child').innerText = `${categorias[cat].length} ítems ${isOp ? '▴' : '▾'}`;
            };
            
            acc.appendChild(header);
            acc.appendChild(content);
            container.appendChild(acc);
        }
    } catch(e) { console.error("Error cargando historial de fecha", e); }
}

async function loadAdminUsuarios() {
    const res = await fetch(`${SERVER_URL}/api/admin/usuarios`, { headers: getAuthHeaders() });
    const data = await res.json();
    const ul = document.getElementById('lista-usuarios');
    ul.innerHTML = '';
    data.forEach(u => {
        const li = document.createElement('li');
        li.innerHTML = `<div><strong>${u.nombre}</strong> (${u.dni}) - <em>${u.rol}</em></div>`;
        const btn = document.createElement('button');
        btn.className = 'btn-delete'; btn.textContent = 'Borrar';
        btn.onclick = async () => {
            if(confirm('¿Borrar usuario?')) {
                await fetch(`${SERVER_URL}/api/admin/usuarios/${u.id}`, {method: 'DELETE', headers: getAuthHeaders()});
                loadAdminUsuarios();
            }
        };
        li.appendChild(btn);
        ul.appendChild(li);
    });
}

async function loadAdminCategorias() {
    const res = await fetch(`${SERVER_URL}/api/admin/categorias`, { headers: getAuthHeaders() });
    const data = await res.json();
    const ul = document.getElementById('lista-categorias');
    ul.innerHTML = '';
    data.forEach(c => {
        const li = document.createElement('li');
        li.innerHTML = `<div>${c.nombre}</div>`;
        const btn = document.createElement('button');
        btn.className = 'btn-delete'; btn.textContent = 'Borrar';
        btn.onclick = async () => {
            if(confirm('¿Borrar categoría?')) {
                await fetch(`${SERVER_URL}/api/admin/categorias/${c.id}`, {method: 'DELETE', headers: getAuthHeaders()});
                loadAdminCategorias();
            }
        };
        li.appendChild(btn);
        ul.appendChild(li);
    });
}

async function loadAdminDiccionario() {
    const res = await fetch(`${SERVER_URL}/api/admin/diccionario`, { headers: getAuthHeaders() });
    const data = await res.json();
    const ul = document.getElementById('lista-diccionario');
    ul.innerHTML = '';
    data.forEach(d => {
        const li = document.createElement('li');
        li.innerHTML = `<div><strong>${d.alias}</strong> = ${d.real_name}</div>`;
        const btn = document.createElement('button');
        btn.className = 'btn-delete'; btn.textContent = 'Borrar';
        btn.onclick = async () => {
            if(confirm('¿Borrar regla?')) {
                await fetch(`${SERVER_URL}/api/admin/diccionario/${d.id}`, {method: 'DELETE', headers: getAuthHeaders()});
                loadAdminDiccionario();
            }
        };
        li.appendChild(btn);
        ul.appendChild(li);
    });
}

window.addEventListener('DOMContentLoaded', init);

// --- PWA Install Logic ---
let deferredPrompt;
const installAppBtn = document.getElementById('install-app-btn');

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Update UI notify the user they can install the PWA
    if (installAppBtn) {
        installAppBtn.classList.remove('hidden');
    }
});

if (installAppBtn) {
    installAppBtn.addEventListener('click', async () => {
        if (deferredPrompt) {
            // Show the install prompt
            deferredPrompt.prompt();
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response to the install prompt: ${outcome}`);
            // We've used the prompt, and can't use it again, throw it away
            deferredPrompt = null;
            installAppBtn.classList.add('hidden');
        }
    });
}

window.addEventListener('appinstalled', () => {
    // Hide the app-provided install promotion
    if (installAppBtn) {
        installAppBtn.classList.add('hidden');
    }
    // Clear the deferredPrompt so it can be garbage collected
    deferredPrompt = null;
    console.log('PWA was installed');
});

// Efecto Parallax en el fondo (Bokeh)
document.addEventListener('mousemove', (e) => {
  const bokehContainer = document.getElementById('bokeh-container');
  if(!bokehContainer) return;
  const x = (e.clientX / window.innerWidth - 0.5) * 20;
  const y = (e.clientY / window.innerHeight - 0.5) * 20;
  bokehContainer.style.transform = `translate(${x}px, ${y}px)`;
});
