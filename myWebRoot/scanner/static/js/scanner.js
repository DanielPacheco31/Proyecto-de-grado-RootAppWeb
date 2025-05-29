// Variables globales
let currentScanType = 'barcode';
let scannerActive = false;
let quaggaInitialized = false;
let stream = null;
let scanningInterval = null;

// Elementos DOM
let elements = {};

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
    setupTypeSelector();
    showInitialMessage();
});

// Inicializar referencias a elementos DOM
function initializeElements() {
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

    // Verificar elementos esenciales
    if (!elements.video || !elements.startButton || !elements.resultDiv) {
        console.error("❌ Elementos esenciales del scanner no encontrados");
        return false;
    }

    return true;
}

// Configurar event listeners
function setupEventListeners() {
    if (elements.startButton) {
        elements.startButton.addEventListener('click', handleStartButton);
    }

    // Prevenir submit accidental del formulario manual
    const manualForm = document.querySelector('.manual-input-form');
    if (manualForm) {
        manualForm.addEventListener('submit', handleManualSubmit);
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
    if (!elements.barcodeOption || !elements.qrcodeOption) return;

    elements.barcodeOption.addEventListener('click', () => {
        if (currentScanType === 'barcode') return;
        
        switchScanType('barcode');
        updateSelectorUI(true);
    });

    elements.qrcodeOption.addEventListener('click', () => {
        if (currentScanType === 'qrcode') return;
        
        switchScanType('qrcode');
        updateSelectorUI(false);
    });
}

// Cambiar tipo de scanner
function switchScanType(newType) {
    const wasActive = scannerActive;
    
    if (wasActive) {
        stopScanner();
    }
    
    currentScanType = newType;
    updateStatusMessage(`Modo ${newType === 'barcode' ? 'Código de Barras' : 'Código QR'} seleccionado`);
    
    if (wasActive) {
        setTimeout(initScanner, 500);
    }
}

// Actualizar UI del selector
function updateSelectorUI(isBarcodeActive) {
    if (!elements.barcodeOption || !elements.qrcodeOption || !elements.selectorPill) return;

    if (isBarcodeActive) {
        elements.barcodeOption.classList.add('active');
        elements.qrcodeOption.classList.remove('active');
        elements.selectorPill.style.transform = 'translateX(0)';
    } else {
        elements.qrcodeOption.classList.add('active');
        elements.barcodeOption.classList.remove('active');
        elements.selectorPill.style.transform = 'translateX(100%)';
    }
}

// Manejar click del botón de inicio
function handleStartButton() {
    if (scannerActive) {
        stopScanner();
    } else {
        initScanner();
    }
}

// Inicializar scanner
async function initScanner() {
    try {
        scannerActive = true;
        updateButtonState(true);
        updateStatusMessage('Iniciando escáner...');
        updateCameraStatus('Solicitando acceso...');
        showOverlay(true);
        hideScanForm();

        // Detener scanner anterior si existe
        stopScanner(false);

        // Solicitar acceso a la cámara
        await requestCameraAccess();
        
        // Configurar scanner según tipo
        if (currentScanType === 'barcode') {
            await setupBarcodeScanner();
        } else {
            setupQRScanner();
        }

        updateStatusMessage(`Apunte a un ${currentScanType === 'barcode' ? 'código de barras' : 'código QR'}`);
        updateCameraStatus('Activa y escaneando');

    } catch (error) {
        console.error('❌ Error inicializando scanner:', error);
        handleScannerError(error);
    }
}

// Solicitar acceso a la cámara
async function requestCameraAccess() {
    const constraints = {
        video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 }
        },
        audio: false
    };

    try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        elements.video.srcObject = stream;
        elements.video.setAttribute('playsinline', true);
        elements.video.setAttribute('muted', true);

        return new Promise((resolve, reject) => {
            elements.video.onloadedmetadata = () => {
                elements.video.play()
                    .then(resolve)
                    .catch(reject);
            };
            elements.video.onerror = reject;
        });

    } catch (error) {
        throw new Error(`No se pudo acceder a la cámara: ${error.message}`);
    }
}

// Configurar scanner de códigos de barras
async function setupBarcodeScanner() {
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
        frequency: 10,
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

    return new Promise((resolve, reject) => {
        Quagga.init(config, (err) => {
            if (err) {
                reject(new Error(`Error inicializando Quagga: ${err.message}`));
                return;
            }

            quaggaInitialized = true;
            Quagga.start();

            // Configurar detección
            Quagga.onDetected(handleBarcodeDetection);
            
            resolve();
        });
    });
}

// Configurar scanner de códigos QR
function setupQRScanner() {
    if (!elements.canvas || !elements.video) return;

    const ctx = elements.canvas.getContext('2d');
    
    function scanQRCode() {
        if (!scannerActive) return;

        try {
            // Verificar que el video esté listo
            if (!elements.video.videoWidth || !elements.video.videoHeight) {
                requestAnimationFrame(scanQRCode);
                return;
            }

            // Configurar canvas
            elements.canvas.width = elements.video.videoWidth;
            elements.canvas.height = elements.video.videoHeight;

            // Dibujar frame actual
            ctx.drawImage(elements.video, 0, 0, elements.canvas.width, elements.canvas.height);

            // Obtener datos de imagen
            const imageData = ctx.getImageData(0, 0, elements.canvas.width, elements.canvas.height);

            // Detectar código QR
            const qrCode = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "attemptBoth"
            });

            if (qrCode && qrCode.data) {
                handleQRDetection(qrCode.data);
                return;
            }

            // Continuar escaneando
            requestAnimationFrame(scanQRCode);

        } catch (error) {
            console.error('❌ Error escaneando QR:', error);
            if (scannerActive) {
                requestAnimationFrame(scanQRCode);
            }
        }
    }

    scanQRCode();
}

// Manejar detección de código de barras
function handleBarcodeDetection(result) {
    if (!scannerActive || !result || !result.codeResult) return;

    const code = result.codeResult.code;
    if (!code || code.length < 3) return;

    console.log('✅ Código de barras detectado:', code);
    handleSuccessfulScan(code);
}

// Manejar detección de código QR
function handleQRDetection(data) {
    if (!scannerActive || !data) return;

    console.log('✅ Código QR detectado:', data);
    handleSuccessfulScan(data);
}

// Manejar escaneo exitoso
function handleSuccessfulScan(code) {
    stopScanner();
    
    updateStatusMessage(`✅ Código detectado: ${code}`, 'success');
    showOverlay(false);
    
    // Rellenar formulario
    if (elements.scannedCodeInput) {
        elements.scannedCodeInput.value = code;
    }
    
    showScanForm();
    
    // Vibración si está disponible
    if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
    }
}

// Detener scanner
function stopScanner(updateUI = true) {
    scannerActive = false;

    // Detener Quagga
    if (quaggaInitialized) {
        try {
            Quagga.stop();
            Quagga.offDetected(handleBarcodeDetection);
            quaggaInitialized = false;
        } catch (error) {
            console.error('❌ Error deteniendo Quagga:', error);
        }
    }

    // Detener stream de cámara
    if (stream) {
        stream.getTracks().forEach(track => {
            track.stop();
        });
        stream = null;
    }

    // Limpiar video
    if (elements.video && elements.video.srcObject) {
        elements.video.srcObject = null;
    }

    // Limpiar interval
    if (scanningInterval) {
        clearInterval(scanningInterval);
        scanningInterval = null;
    }

    if (updateUI) {
        updateButtonState(false);
        updateCameraStatus('Detenida');
        showOverlay(false);
    }
}

// Manejar errores del scanner
function handleScannerError(error) {
    console.error('❌ Error del scanner:', error);
    
    stopScanner();
    updateStatusMessage(`❌ Error: ${error.message}`, 'error');
    updateCameraStatus('Error');
    showOverlay(false);
}

// Manejar submit manual
function handleManualSubmit(event) {
    const input = event.target.querySelector('input[name="scannedCode"]');
    const code = input ? input.value.trim() : '';
    
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
}

// Funciones de UI
function updateButtonState(isActive) {
    if (!elements.startButton) return;
    
    if (isActive) {
        elements.startButton.textContent = 'Detener escáner';
        elements.startButton.disabled = false;
        elements.startButton.classList.add('active');
    } else {
        elements.startButton.textContent = 'Iniciar escáner';
        elements.startButton.disabled = false;
        elements.startButton.classList.remove('active');
    }
}

function updateStatusMessage(message, type = '') {
    if (!elements.resultDiv) return;
    
    elements.resultDiv.textContent = message;
    elements.resultDiv.className = type;
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
    }
}

function hideScanForm() {
    if (elements.scanForm) {
        elements.scanForm.style.display = 'none';
    }
}

// Limpiar recursos
function cleanup() {
    stopScanner(false);
}

// Verificar soporte del navegador
function checkBrowserSupport() {
    const errors = [];
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        errors.push('La cámara no es compatible con este navegador');
    }
    
    if (typeof Quagga === 'undefined') {
        errors.push('Librería de códigos de barras no cargada');
    }
    
    if (typeof jsQR === 'undefined') {
        errors.push('Librería de códigos QR no cargada');
    }
    
    return errors;
}

// Mostrar errores de compatibilidad
function showCompatibilityErrors() {
    const errors = checkBrowserSupport();
    
    if (errors.length > 0) {
        updateStatusMessage(`❌ Errores de compatibilidad: ${errors.join(', ')}`, 'error');
        if (elements.startButton) {
            elements.startButton.disabled = true;
        }
        return false;
    }
    
    return true;
}

// Verificar compatibilidad cuando las librerías se carguen
window.addEventListener('load', () => {
    setTimeout(() => {
        if (!showCompatibilityErrors()) {
            console.error('❌ Scanner no compatible con este navegador');
        } else {
            console.log('✅ Scanner inicializado correctamente');
        }
    }, 1000);
});