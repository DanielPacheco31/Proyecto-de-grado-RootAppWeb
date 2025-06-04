console.log('🚀 Scanner ROOT v2.1 - Detención Corregida');

// Variables globales
let currentScanType = 'barcode';
let scannerActive = false;
let quaggaInitialized = false;
let stream = null;
let scanningInterval = null;
let qrScanActive = false;
let qrAnimationFrame = null; // NUEVA: para controlar requestAnimationFrame

// Elementos DOM
let elements = {};

// Función de logging mejorada
function debugLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const emoji = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'debug': '🔍'
    }[type] || 'ℹ️';
    
    console.log(`${emoji} [${timestamp}] ${message}`);
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    debugLog('DOM cargado, inicializando scanner', 'success');
    
    // Verificar que las librerías estén cargadas
    setTimeout(() => {
        checkLibraries();
        initializeElements();
        setupEventListeners();
        setupTypeSelector();
        showInitialMessage();
    }, 100);
});

// Verificar librerías
function checkLibraries() {
    if (typeof Quagga === 'undefined') {
        debugLog('ERROR: Quagga no está cargada', 'error');
        updateStatusMessage('❌ Error: Librería Quagga no cargada', 'error');
        return false;
    }
    
    if (typeof jsQR === 'undefined') {
        debugLog('ERROR: jsQR no está cargada', 'error');
        updateStatusMessage('❌ Error: Librería jsQR no cargada', 'error');
        return false;
    }
    
    debugLog('Librerías cargadas correctamente', 'success');
    return true;
}

// Inicializar referencias a elementos DOM
function initializeElements() {
    debugLog('Inicializando elementos DOM', 'info');
    
    elements = {
        video: document.getElementById('video'),
        canvas: document.getElementById('canvas'),
        startButton: document.getElementById('startButton'),
        resultDiv: document.getElementById('result'),
        scanForm: document.getElementById('scanForm'),
        scannedCodeInput: document.getElementById('scannedCode'),
        cameraStatus: document.getElementById('cameraStatus'),
        scannerOverlay: document.getElementById('scannerOverlay'),
        barcodeOption: document.getElementById('barcodeOption'),
        qrcodeOption: document.getElementById('qrcodeOption'),
        selectorPill: document.getElementById('selectorPill')
    };

    // Verificar elementos críticos
    const criticalElements = ['video', 'canvas', 'startButton', 'resultDiv'];
    const missing = criticalElements.filter(key => !elements[key]);
    
    if (missing.length > 0) {
        debugLog(`ERROR: Elementos críticos faltantes: ${missing.join(', ')}`, 'error');
        return false;
    }

    debugLog('Todos los elementos DOM encontrados', 'success');
    return true;
}

// Configurar event listeners
function setupEventListeners() {
    if (elements.startButton) {
        elements.startButton.addEventListener('click', handleStartButton);
        debugLog('Event listener agregado al botón start', 'info');
    }

    // Prevenir submit accidental del formulario manual
    const manualForm = document.querySelector('.manual-input-form');
    if (manualForm) {
        manualForm.addEventListener('submit', handleManualSubmit);
        debugLog('Event listener agregado al formulario manual', 'info');
    }

    // Limpiar recursos al salir de la página
    window.addEventListener('beforeunload', cleanup);
}

// Mostrar mensaje inicial
function showInitialMessage() {
    if (elements.resultDiv) {
        elements.resultDiv.textContent = 'Presiona "Iniciar escáner" para comenzar';
        elements.resultDiv.className = '';
    }
}

// Configurar selector de tipo de scanner
function setupTypeSelector() {
    if (!elements.barcodeOption || !elements.qrcodeOption) {
        debugLog('Selectores de tipo no encontrados', 'warning');
        return;
    }

    elements.barcodeOption.addEventListener('click', () => {
        if (currentScanType === 'barcode') return;
        debugLog('Cambiando a modo código de barras', 'info');
        switchScanType('barcode');
        updateSelectorUI(true);
    });

    elements.qrcodeOption.addEventListener('click', () => {
        if (currentScanType === 'qrcode') return;
        debugLog('Cambiando a modo código QR', 'info');
        switchScanType('qrcode');
        updateSelectorUI(false);
    });
}

// Cambiar tipo de scanner
function switchScanType(newType) {
    const wasActive = scannerActive;
    
    if (wasActive) {
        debugLog('Deteniendo scanner para cambio de tipo', 'info');
        stopScanner();
    }
    
    currentScanType = newType;
    updateStatusMessage(`Modo ${newType === 'barcode' ? 'Código de Barras' : 'Código QR'} seleccionado`);
    
    if (wasActive) {
        setTimeout(() => {
            debugLog('Reiniciando scanner con nuevo tipo', 'info');
            initScanner();
        }, 500);
    }
}

// Actualizar UI del selector
function updateSelectorUI(isBarcodeActive) {
    if (!elements.barcodeOption || !elements.qrcodeOption || !elements.selectorPill) return;

    if (isBarcodeActive) {
        elements.barcodeOption.classList.add('active');
        elements.qrcodeOption.classList.remove('active');
        if (elements.selectorPill) {
            elements.selectorPill.style.transform = 'translateX(0)';
        }
    } else {
        elements.qrcodeOption.classList.add('active');
        elements.barcodeOption.classList.remove('active');
        if (elements.selectorPill) {
            elements.selectorPill.style.transform = 'translateX(100%)';
        }
    }
}

// Manejar click del botón de inicio
function handleStartButton() {
    debugLog(`Botón presionado. Scanner activo: ${scannerActive}`, 'info');
    
    if (scannerActive) {
        debugLog('Deteniendo scanner por click del usuario', 'info');
        stopScanner();
    } else {
        debugLog('Iniciando scanner por click del usuario', 'info');
        initScanner();
    }
}

// Inicializar scanner
async function initScanner() {
    debugLog('Iniciando scanner...', 'info');
    
    try {
        // Verificar librerías primero
        if (!checkLibraries()) {
            throw new Error('Librerías no disponibles');
        }
        
        scannerActive = true;
        updateButtonState(true);
        updateStatusMessage('Iniciando escáner...');
        updateCameraStatus('Solicitando acceso...');
        showOverlay(true);
        hideScanForm();

        // Detener scanner anterior si existe
        await forceStopAllScanners();

        // Solicitar acceso a la cámara
        debugLog('Solicitando acceso a cámara', 'info');
        await requestCameraAccess();
        
        // Configurar scanner según tipo
        if (currentScanType === 'barcode') {
            debugLog('Configurando scanner de códigos de barras', 'info');
            await setupBarcodeScanner();
        } else {
            debugLog('Configurando scanner de códigos QR', 'info');
            setupQRScanner();
        }

        updateStatusMessage(`Apunte a un ${currentScanType === 'barcode' ? 'código de barras' : 'código QR'}`);
        updateCameraStatus('Activa y escaneando');
        debugLog('Scanner inicializado correctamente', 'success');

    } catch (error) {
        debugLog(`Error inicializando scanner: ${error.message}`, 'error');
        handleScannerError(error);
    }
}

// NUEVA FUNCIÓN: Forzar detención de todos los scanners
async function forceStopAllScanners() {
    debugLog('Forzando detención de todos los scanners', 'info');
    
    // Detener QR scanner
    qrScanActive = false;
    if (qrAnimationFrame) {
        cancelAnimationFrame(qrAnimationFrame);
        qrAnimationFrame = null;
        debugLog('QR animation frame cancelado', 'info');
    }
    
    // Detener Quagga
    if (quaggaInitialized) {
        try {
            debugLog('Deteniendo Quagga...', 'info');
            Quagga.stop();
            Quagga.offDetected();
            Quagga.offProcessed();
            quaggaInitialized = false;
            debugLog('Quagga detenido correctamente', 'success');
        } catch (error) {
            debugLog(`Error deteniendo Quagga: ${error.message}`, 'error');
        }
    }

    // Detener stream de cámara
    if (stream) {
        debugLog('Deteniendo stream de cámara...', 'info');
        stream.getTracks().forEach(track => {
            track.stop();
            debugLog(`Track detenido: ${track.kind} - estado: ${track.readyState}`, 'info');
        });
        stream = null;
    }

    // Limpiar video
    if (elements.video && elements.video.srcObject) {
        elements.video.srcObject = null;
        debugLog('Video source object limpiado', 'info');
    }

    // Limpiar interval
    if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
        debugLog('Scanning interval limpiado', 'info');
    }

    // Pequeña pausa para asegurar limpieza
    await new Promise(resolve => setTimeout(resolve, 100));
    debugLog('Limpieza completa terminada', 'success');
}

// Solicitar acceso a la cámara
async function requestCameraAccess() {
    debugLog('Verificando soporte de MediaDevices', 'info');
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Tu navegador no soporta acceso a cámara');
    }

    const constraints = {
        video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 }
        },
        audio: false
    };

    debugLog(`Constraints: ${JSON.stringify(constraints)}`, 'debug');

    try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        debugLog('Stream obtenido exitosamente', 'success');
        
        elements.video.srcObject = stream;
        elements.video.setAttribute('playsinline', true);
        elements.video.setAttribute('muted', true);

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                debugLog('Timeout esperando metadata del video', 'error');
                reject(new Error('Timeout cargando video'));
            }, 10000);
            
            elements.video.onloadedmetadata = () => {
                clearTimeout(timeout);
                debugLog(`Video metadata: ${elements.video.videoWidth}x${elements.video.videoHeight}`, 'success');
                
                elements.video.play()
                    .then(() => {
                        debugLog('Video reproduciendo correctamente', 'success');
                        resolve(stream);
                    })
                    .catch(err => {
                        debugLog(`Error reproduciendo video: ${err.message}`, 'error');
                        reject(err);
                    });
            };
            
            elements.video.onerror = (err) => {
                clearTimeout(timeout);
                debugLog(`Error en elemento video: ${err}`, 'error');
                reject(new Error('Error en elemento video'));
            };
        });

    } catch (error) {
        debugLog(`Error obteniendo stream: ${error.name} - ${error.message}`, 'error');
        
        // Información específica del error
        let errorMessage = 'Error accediendo a la cámara';
        switch (error.name) {
            case 'NotAllowedError':
                errorMessage = 'Permisos de cámara denegados. Por favor permite el acceso.';
                break;
            case 'NotFoundError':
                errorMessage = 'No se encontró ninguna cámara en tu dispositivo.';
                break;
            case 'NotSupportedError':
                errorMessage = 'Tu navegador no soporta acceso a cámara.';
                break;
            case 'OverconstrainedError':
                errorMessage = 'La cámara no cumple los requisitos solicitados.';
                break;
        }
        
        throw new Error(errorMessage);
    }
}

// Configurar scanner de códigos de barras
async function setupBarcodeScanner() {
    debugLog('Configurando Quagga para códigos de barras', 'info');
    
    if (!elements.video || !elements.video.videoWidth) {
        throw new Error('Video no está listo para Quagga');
    }

    const config = {
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: elements.video,
            constraints: {
                width: { min: 640, ideal: 1280 },
                height: { min: 480, ideal: 720 },
                facingMode: "environment"
            }
        },
        locator: {
            patchSize: "medium",
            halfSample: true
        },
        frequency: 10, // Procesar cada 10 frames
        decoder: {
            readers: [
                "ean_reader",
                "ean_8_reader", 
                "code_128_reader",
                "code_39_reader",
                "upc_reader",
                "upc_e_reader"
            ]
        },
        locate: true
    };

    debugLog(`Configuración Quagga: ${JSON.stringify(config, null, 2)}`, 'debug');

    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            debugLog('Timeout inicializando Quagga', 'error');
            reject(new Error('Timeout en inicialización de Quagga'));
        }, 15000);
        
        Quagga.init(config, (err) => {
            clearTimeout(timeout);
            
            if (err) {
                debugLog(`Error Quagga init: ${err.message}`, 'error');
                reject(new Error(`Error inicializando Quagga: ${err.message}`));
                return;
            }

            debugLog('Quagga inicializado, configurando eventos', 'success');
            quaggaInitialized = true;
            
            try {
                Quagga.start();
                debugLog('Quagga iniciado correctamente', 'success');

                // Configurar detección con logging
                Quagga.onDetected((result) => {
                    debugLog('¡Evento onDetected disparado!', 'info');
                    
                    if (!scannerActive || !result || !result.codeResult) {
                        debugLog('Detección ignorada (scanner inactivo o resultado inválido)', 'warning');
                        return;
                    }

                    const code = result.codeResult.code;
                    const quality = result.codeResult.quality || 0;
                    
                    debugLog(`Código detectado: "${code}" (calidad: ${quality})`, 'success');
                    
                    // Filtrar códigos de baja calidad
                    if (quality < 50) {
                        debugLog(`Código rechazado por baja calidad: ${quality}`, 'warning');
                        return;
                    }
                    
                    if (!code || code.length < 3) {
                        debugLog(`Código rechazado por longitud: "${code}"`, 'warning');
                        return;
                    }

                    handleSuccessfulScan(code);
                });

                // Log de procesamiento (reducido para no saturar)
                let frameCount = 0;
                Quagga.onProcessed((result) => {
                    frameCount++;
                    if (frameCount % 100 === 0) { // Log cada 100 frames
                        debugLog(`Frames procesados: ${frameCount}`, 'debug');
                    }
                });
                
                resolve();
                
            } catch (startError) {
                debugLog(`Error iniciando Quagga: ${startError.message}`, 'error');
                reject(startError);
            }
        });
    });
}

// Configurar scanner de códigos QR - VERSIÓN CORREGIDA
function setupQRScanner() {
    debugLog('Configurando scanner QR con jsQR', 'info');
    
    if (!elements.canvas || !elements.video) {
        throw new Error('Canvas o video no disponibles para QR');
    }

    const ctx = elements.canvas.getContext('2d');
    if (!ctx) {
        throw new Error('No se pudo obtener contexto 2D del canvas');
    }
    
    qrScanActive = true;
    let frameCount = 0;
    
    function scanQRCode() {
        // VERIFICACIÓN CRÍTICA: Solo continuar si el scanner sigue activo
        if (!qrScanActive || !scannerActive) {
            debugLog('Scanner QR detenido - saliendo del bucle', 'info');
            qrAnimationFrame = null;
            return;
        }

        try {
            // Verificar que el video esté listo
            if (!elements.video.videoWidth || !elements.video.videoHeight) {
                qrAnimationFrame = requestAnimationFrame(scanQRCode);
                return;
            }

            frameCount++;
            
            // Log cada 200 frames para no saturar
            if (frameCount % 200 === 0) {
                debugLog(`Frames QR procesados: ${frameCount}`, 'debug');
            }

            // Configurar canvas con las dimensiones del video
            elements.canvas.width = elements.video.videoWidth;
            elements.canvas.height = elements.video.videoHeight;

            // Dibujar frame actual
            ctx.drawImage(elements.video, 0, 0, elements.canvas.width, elements.canvas.height);

            // Obtener datos de imagen
            const imageData = ctx.getImageData(0, 0, elements.canvas.width, elements.canvas.height);

            // Detectar código QR con opciones mejoradas
            const qrCode = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "attemptBoth"
            });

            if (qrCode && qrCode.data) {
                debugLog(`QR detectado: "${qrCode.data}"`, 'success');
                debugLog(`Posición QR: ${JSON.stringify(qrCode.location)}`, 'debug');
                
                if (qrCode.data.length >= 3) {
                    handleSuccessfulScan(qrCode.data);
                    return; // IMPORTANTE: salir del bucle después de detectar
                } else {
                    debugLog(`QR rechazado por longitud: "${qrCode.data}"`, 'warning');
                }
            }

            // Continuar escaneando SOLO si el scanner sigue activo
            if (qrScanActive && scannerActive) {
                qrAnimationFrame = requestAnimationFrame(scanQRCode);
            } else {
                debugLog('Scanner QR detenido durante escaneo', 'info');
                qrAnimationFrame = null;
            }

        } catch (error) {
            debugLog(`Error escaneando QR: ${error.message}`, 'error');
            if (qrScanActive && scannerActive && frameCount < 10000) { 
                qrAnimationFrame = requestAnimationFrame(scanQRCode);
            } else {
                debugLog('Deteniendo scanner QR por error o límite alcanzado', 'error');
                qrScanActive = false;
                qrAnimationFrame = null;
            }
        }
    }

    debugLog('Iniciando bucle de escaneo QR', 'info');
    qrAnimationFrame = requestAnimationFrame(scanQRCode); // GUARDAMOS la referencia
}

// Manejar escaneo exitoso
function handleSuccessfulScan(code) {
    debugLog(`¡CÓDIGO ESCANEADO EXITOSAMENTE: "${code}"!`, 'success');
    
    stopScanner();
    
    updateStatusMessage(`✅ Código detectado: ${code}`, 'success');
    showOverlay(false);
    
    // Rellenar formulario
    if (elements.scannedCodeInput) {
        elements.scannedCodeInput.value = code;
        debugLog('Código establecido en formulario', 'success');
    }
    
    showScanForm();
    
    // Vibración si está disponible
    if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
        debugLog('Vibración activada', 'info');
    }
    
    // Reproducir sonido de éxito (opcional)
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTuR1/LNeCsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBT');
        audio.play().catch(() => {}); // Ignorar errores
    } catch (e) {
        // Ignorar errores de audio
    }
}

// Detener scanner - VERSIÓN CORREGIDA
function stopScanner(updateUI = true) {
    debugLog('=== INICIANDO DETENCIÓN DEL SCANNER ===', 'info');
    
    // PASO 1: Marcar como inactivo INMEDIATAMENTE
    scannerActive = false;
    qrScanActive = false;
    debugLog('Variables de estado marcadas como inactivas', 'info');

    // PASO 2: Cancelar animation frame QR
    if (qrAnimationFrame) {
        cancelAnimationFrame(qrAnimationFrame);
        qrAnimationFrame = null;
        debugLog('QR animation frame cancelado', 'success');
    }

    // PASO 3: Detener Quagga
    if (quaggaInitialized) {
        try {
            debugLog('Deteniendo Quagga...', 'info');
            Quagga.stop();
            Quagga.offDetected();
            Quagga.offProcessed();
            quaggaInitialized = false;
            debugLog('Quagga detenido correctamente', 'success');
        } catch (error) {
            debugLog(`Error deteniendo Quagga: ${error.message}`, 'error');
        }
    }

    // PASO 4: Detener stream de cámara
    if (stream) {
        debugLog('Deteniendo stream de cámara...', 'info');
        stream.getTracks().forEach(track => {
            track.stop();
            debugLog(`Track detenido: ${track.kind} - estado: ${track.readyState}`, 'info');
        });
        stream = null;
        debugLog('Stream de cámara limpiado', 'success');
    }

    // PASO 5: Limpiar video
    if (elements.video && elements.video.srcObject) {
        elements.video.srcObject = null;
        debugLog('Video source object limpiado', 'info');
    }

    // PASO 6: Limpiar interval (por si acaso)
    if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
        debugLog('Scanning interval limpiado', 'info');
    }

    // PASO 7: Actualizar UI si se solicita
    if (updateUI) {
        updateButtonState(false);
        updateCameraStatus('Detenida');
        showOverlay(false);
        updateStatusMessage('Scanner detenido. Presiona "Iniciar escáner" para volver a empezar.');
        debugLog('UI actualizada', 'info');
    }

    debugLog('=== DETENCIÓN DEL SCANNER COMPLETA ===', 'success');
}

// Manejar errores del scanner
function handleScannerError(error) {
    debugLog(`Error del scanner: ${error.message}`, 'error');
    
    stopScanner();
    updateStatusMessage(`❌ Error: ${error.message}`, 'error');
    updateCameraStatus('Error');
    showOverlay(false);
}

// Manejar submit manual
function handleManualSubmit(event) {
    const input = event.target.querySelector('input[name="scannedCode"]');
    const code = input ? input.value.trim() : '';
    
    debugLog(`Submit manual con código: "${code}"`, 'info');
    
    if (!code) {
        event.preventDefault();
        updateStatusMessage('❌ Por favor ingrese un código válido', 'error');
        return false;
    }
    
    if (code.length < 3) {
        event.preventDefault();
        updateStatusMessage('❌ El código debe tener al menos 3 caracteres', 'error');
        return false;
    }
    
    updateStatusMessage(`✅ Código ingresado: ${code}`, 'success');
    debugLog('Formulario manual enviado correctamente', 'success');
}

// Funciones de UI
function updateButtonState(isActive) {
    if (!elements.startButton) return;
    
    if (isActive) {
        elements.startButton.textContent = 'Detener escáner';
        elements.startButton.disabled = false;
        elements.startButton.classList.add('active');
        debugLog('Botón actualizado a estado ACTIVO', 'info');
    } else {
        elements.startButton.textContent = 'Iniciar escáner';
        elements.startButton.disabled = false;
        elements.startButton.classList.remove('active');
        debugLog('Botón actualizado a estado INACTIVO', 'info');
    }
}

function updateStatusMessage(message, type = '') {
    if (!elements.resultDiv) return;
    
    elements.resultDiv.textContent = message;
    elements.resultDiv.className = type;
    debugLog(`Status actualizado: ${message}`, 'info');
}

function updateCameraStatus(status) {
    if (!elements.cameraStatus) return;
    
    const statusSpan = elements.cameraStatus.querySelector('span');
    if (statusSpan) {
        statusSpan.textContent = status;
    }
}

function showOverlay(show) {
    if (!elements.scannerOverlay) return;
    
    elements.scannerOverlay.style.display = show ? 'block' : 'none';
}

function showScanForm() {
    if (elements.scanForm) {
        elements.scanForm.style.display = 'block';
        debugLog('Formulario de scan mostrado', 'info');
    }
}

function hideScanForm() {
    if (elements.scanForm) {
        elements.scanForm.style.display = 'none';
    }
}

// Limpiar recursos
function cleanup() {
    debugLog('Limpiando recursos al cerrar página', 'info');
    stopScanner(false);
}

// Verificar soporte del navegador al cargar
window.addEventListener('load', () => {
    setTimeout(() => {
        debugLog('Verificando compatibilidad del navegador', 'info');
        
        const errors = [];
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            errors.push('MediaDevices API no compatible');
        }
        
        if (typeof Quagga === 'undefined') {
            errors.push('Librería Quagga no cargada');
        }
        
        if (typeof jsQR === 'undefined') {
            errors.push('Librería jsQR no cargada');
        }
        
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            errors.push('Se requiere HTTPS para acceso a cámara');
        }
        
        if (errors.length > 0) {
            debugLog(`Errores de compatibilidad: ${errors.join(', ')}`, 'error');
            updateStatusMessage(`❌ Problemas detectados: ${errors.join(', ')}`, 'error');
            if (elements.startButton) {
                elements.startButton.disabled = true;
            }
        } else {
            debugLog('✅ Navegador compatible, scanner listo', 'success');
        }
    }, 1000);
});

// Exponer funciones para debug manual
window.scannerDebug = {
    elements,
    scannerActive,
    currentScanType,
    qrScanActive,
    quaggaInitialized,
    initScanner,
    stopScanner,
    forceStopAllScanners,
    debugLog
};

debugLog('Scanner v2.1 cargado y listo - Problema de detención solucionado', 'success');;