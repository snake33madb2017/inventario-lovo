// Constantes y Variables Globales
let SERVER_URL = window.location.origin;

let isListening = false;
let recognition = null;
let recentItems = [];
let historicoProductos = [];
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
const toast = document.getElementById('toast');

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
    showLogin();
}

function showApp(userName, userRol) {
    loginView.classList.remove('active');
    loginView.classList.add('hidden');
    appView.classList.remove('hidden');
    appView.classList.add('active');
    adminView.classList.add('hidden');
    
    userDisplay.textContent = userName + (userRol === 'encargado' ? ' (Encargado)' : ' (Camarero)');
    
    if(userRol === 'encargado') {
        adminToggleBtn.classList.remove('hidden');
        downloadBtn.classList.remove('hidden');
        clearMonthBtn.classList.remove('hidden');
    } else {
        adminToggleBtn.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        clearMonthBtn.classList.add('hidden');
    }
    
    checkServerConnection();
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
    const currentIp = SERVER_URL.replace('http://', '').replace(':8000', '');
    const ip = prompt("Introduce la IP local del servidor backend (Ej: 192.168.1.50 o localhost):", currentIp);
    if (ip) {
        SERVER_URL = `http://${ip}:8000`;
        localStorage.setItem('server_url', SERVER_URL);
        checkServerConnection();
    }
}

function setupServerUrl() {
    if (!localStorage.getItem('server_url') || localStorage.getItem('server_url').includes('192.168.1.:8000')) {
        forceSetupServerUrl();
    }
}

async function checkServerConnection() {
    try {
        await fetch(`${SERVER_URL}/docs`, { mode: 'no-cors' }); 
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
        const response = await fetch(`${SERVER_URL}/api/admin/categorias`);
        if(response.ok) {
            const data = await response.json();
            categorias = data.map(c => c.nombre);
            renderCategorias();
        }
    } catch(e) { console.error("Error cargando categorias", e); }
}

async function fetchDiccionario() {
    try {
        const response = await fetch(`${SERVER_URL}/api/admin/diccionario`);
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

function normalizeText(text) {
    let t = text;
    t = t.replace(/\b(punto|coma)\b/g, '.');
    t = t.replace(/\b(un|una|uno)\b/g, '1');
    t = t.replace(/\b(dos)\b/g, '2');
    t = t.replace(/\b(tres)\b/g, '3');
    t = t.replace(/\b(cuatro)\b/g, '4');
    t = t.replace(/\b(cinco)\b/g, '5');
    t = t.replace(/\b(seis)\b/g, '6');
    t = t.replace(/\b(siete)\b/g, '7');
    t = t.replace(/\b(ocho)\b/g, '8');
    t = t.replace(/\b(nueve)\b/g, '9');
    t = t.replace(/\b(cero)\b/g, '0');
    t = t.replace(/\s+\.\s+/g, '.');
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
    const threshold = 2;
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
        const response = await fetch(`${SERVER_URL}/api/inventario/hoy`);
        if (response.ok) {
            const data = await response.json();
            recentItems = data.registros || [];
            renderList();
        }
    } catch (error) {}
}

async function fetchProductosHistoricos() {
    try {
        const response = await fetch(`${SERVER_URL}/api/productos`);
        if (response.ok) {
            const data = await response.json();
            historicoProductos = data.productos || [];
        }
    } catch (error) {}
}

function downloadExcel() {
    window.location.href = `${SERVER_URL}/api/descargar/hoy`;
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
            headers: { 'Content-Type': 'application/json' },
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
        const response = await fetch(`${SERVER_URL}/api/registro/ultimo`, { method: 'DELETE' });
        if (response.ok) {
            fetchInventarioHoy();
            showToast("Registro borrado");
        }
    } catch (error) {}
}

async function clearMonthInventory() {
    if (confirm("⚠️ ¿ESTÁS SEGURO?\n\nEsto borrará TODO el inventario de la base de datos para empezar un nuevo mes.\n\n¡Asegúrate de haber descargado el Excel antes!")) {
        try {
            const response = await fetch(`${SERVER_URL}/api/inventario/todo`, { method: 'DELETE' });
            if (response.ok) {
                fetchInventarioHoy();
                historicoProductos = [];
                alert("Inventario borrado por completo.");
            }
        } catch (error) {}
    }
}

function renderList() {
    itemsList.innerHTML = '';
    const activeCategory = categoryDropdown.value;
    const filteredItems = recentItems.filter(item => item.categoria === activeCategory);
    
    if (filteredItems.length === 0) {
        itemsList.innerHTML = `<li class="item-card" style="justify-content: center; color: var(--text-muted); font-style: italic;">Sin registros de ${activeCategory} hoy</li>`;
        undoBtn.disabled = true;
        return;
    }
    undoBtn.disabled = false;
    filteredItems.forEach(item => {
        const li = document.createElement('li');
        li.className = 'item-card';
        li.innerHTML = `
            <div class="item-info">
                <span class="item-name">${item.producto}</span>
                <span class="item-category">${item.categoria} &bull; ${item.hora}</span>
            </div>
            <div class="item-quantity">${item.cantidad_dictada}</div>
        `;
        itemsList.appendChild(li);
    });
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
        loadAdminData();
    } else {
        adminView.classList.add('hidden');
        appView.classList.remove('hidden');
        checkServerConnection(); // Reload user side data (cats, dictionary)
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
            method: 'POST', headers: {'Content-Type': 'application/json'},
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
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ nombre: document.getElementById('new-cat-nombre').value })
        });
        e.target.reset();
        loadAdminCategorias();
    });
    
    document.getElementById('form-diccionario').addEventListener('submit', async (e) => {
        e.preventDefault();
        await fetch(`${SERVER_URL}/api/admin/diccionario`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                alias: document.getElementById('new-dict-alias').value,
                real_name: document.getElementById('new-dict-real').value
            })
        });
        e.target.reset();
        loadAdminDiccionario();
    });
}

function loadAdminData() {
    loadAdminUsuarios();
    loadAdminCategorias();
    loadAdminDiccionario();
}

async function loadAdminUsuarios() {
    const res = await fetch(`${SERVER_URL}/api/admin/usuarios`);
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
                await fetch(`${SERVER_URL}/api/admin/usuarios/${u.id}`, {method: 'DELETE'});
                loadAdminUsuarios();
            }
        };
        li.appendChild(btn);
        ul.appendChild(li);
    });
}

async function loadAdminCategorias() {
    const res = await fetch(`${SERVER_URL}/api/admin/categorias`);
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
                await fetch(`${SERVER_URL}/api/admin/categorias/${c.id}`, {method: 'DELETE'});
                loadAdminCategorias();
            }
        };
        li.appendChild(btn);
        ul.appendChild(li);
    });
}

async function loadAdminDiccionario() {
    const res = await fetch(`${SERVER_URL}/api/admin/diccionario`);
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
                await fetch(`${SERVER_URL}/api/admin/diccionario/${d.id}`, {method: 'DELETE'});
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
