document.addEventListener('DOMContentLoaded', () => {
    // Elementos DOM esenciales
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const startButton = document.getElementById('startButton');
    const resultDiv = document.getElementById('result');
    const scanForm = document.getElementById('scanForm');
    const scannedCodeInput = document.getElementById('scannedCode');
    const cameraStatus = document.getElementById('cameraStatus');
    const scannerOverlay = document.getElementById('scannerOverlay');

    // Verificación básica
    if (!video || !startButton || !resultDiv) {
        console.error("Elementos esenciales no encontrados");
        return;
    }

    // Variables globales
    let currentScanType = 'barcode';
    let scannerActive = false;
    let quaggaInitialized = false;

    // Configuración de Quagga simplificada y optimizada
    const quaggaConfig = {
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: video,
            constraints: {
                width: { min: 640, ideal: 1280, max: 1920 },
                height: { min: 480, ideal: 720, max: 1080 },
                aspectRatio: { min: 1, max: 2 },
                facingMode: "environment"
            },
            area: { top: "0%", right: "0%", left: "0%", bottom: "0%" } // Escanear toda el área
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

    // Configuración del selector de tipo
    function setupTypeSelector() {
        const barcodeOption = document.getElementById('barcodeOption');
        const qrcodeOption = document.getElementById('qrcodeOption');
        const selectorPill = document.getElementById('selectorPill');
        
        if (barcodeOption && qrcodeOption) {
            barcodeOption.addEventListener('click', () => {
                currentScanType = 'barcode';
                barcodeOption.classList.add('active');
                qrcodeOption.classList.remove('active');
                if (selectorPill) selectorPill.style.transform = 'translateX(0)';
                
                if (scannerActive) {
                    stopScanner();
                    setTimeout(initScanner, 300);
                }
            });

            qrcodeOption.addEventListener('click', () => {
                currentScanType = 'qrcode';
                qrcodeOption.classList.add('active');
                barcodeOption.classList.remove('active');
                if (selectorPill) selectorPill.style.transform = 'translateX(100%)';
                
                if (scannerActive) {
                    stopScanner();
                    setTimeout(initScanner, 300);
                }
            });
        }
    }

    // Detener scanner
    function stopScanner() {
        scannerActive = false;
        
        if (quaggaInitialized) {
            try {
                Quagga.stop();
                quaggaInitialized = false;
            } catch (e) {
                console.error("Error al detener Quagga:", e);
            }
        }

        if (video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null;
        }
    }

    // Iniciar scanner
    function initScanner() {
        scannerActive = true;
        startButton.disabled = true;
        resultDiv.textContent = 'Iniciando escáner...';
        scanForm.style.display = 'none';
        
        if (scannerOverlay) scannerOverlay.style.display = 'block';
        if (cameraStatus) cameraStatus.querySelector('span').textContent = 'Solicitando acceso...';
        
        stopScanner();
        
        // Opciones de cámara simplificadas
        const constraints = {
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        };
        
        // Intentar acceder a la cámara directamente con opciones flexibles
        navigator.mediaDevices.getUserMedia(constraints)
            .then(stream => {
                video.srcObject = stream;
                video.setAttribute('playsinline', true);
                
                if (cameraStatus) {
                    cameraStatus.querySelector('span').textContent = 'Activa';
                }
                
                video.onloadedmetadata = () => {
                    video.play().then(() => {
                        setupScanner();
                    }).catch(err => {
                        console.error("Error reproduciendo video:", err);
                        handleError(err);
                    });
                };
            })
            .catch(err => {
                console.error("Error accediendo a la cámara:", err);
                handleError(err);
            });
    }

    // Configurar scanner según tipo seleccionado
    function setupScanner() {
        if (currentScanType === 'barcode') {
            setupBarcodeScanner();
        } else {
            setupQRScanner();
        }
    }

    // Configurar scanner de códigos de barras
    function setupBarcodeScanner() {
        Quagga.init(quaggaConfig, function(err) {
            if (err) {
                console.error("Error inicializando Quagga:", err);
                handleError(err);
                return;
            }
            
            quaggaInitialized = true;
            Quagga.start();
            
            // Eventos simplificados
            Quagga.onDetected(result => {
                if (!scannerActive) return;
                
                const code = result.codeResult.code;
                if (!code) return;
                
                console.log("Código detectado:", code);
                handleScannedCode(code);
            });
            
            startButton.disabled = false;
            resultDiv.textContent = 'Apunte a un código de barras';
        });
    }

    // Configurar scanner de QR
    function setupQRScanner() {
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        
        startButton.disabled = false;
        resultDiv.textContent = 'Apunte a un código QR';
        
        function scanQR() {
            if (!scannerActive) return;
            
            try {
                if (!video.videoWidth) {
                    requestAnimationFrame(scanQR);
                    return;
                }

                // Actualizar dimensiones si es necesario
                if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                }
                
                // Dibujar video en canvas
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                // Obtener datos de imagen
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                
                // Intentar detectar QR
                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "attemptBoth"
                });
                
                if (code && code.data) {
                    console.log("QR detectado:", code.data);
                    handleScannedCode(code.data);
                    return;
                }
                
                // Continuar escaneando
                requestAnimationFrame(scanQR);
            } catch (error) {
                console.error("Error escaneando QR:", error);
                if (scannerActive) {
                    requestAnimationFrame(scanQR);
                }
            }
        }
        
        scanQR();
    }

    // Manejar errores
    function handleError(err) {
        if (resultDiv) {
            resultDiv.textContent = 'Error: ' + (err.message || 'No se pudo acceder a la cámara');
            resultDiv.className = 'error';
        }
        
        if (cameraStatus) {
            cameraStatus.querySelector('span').textContent = 'Error';
        }
        
        startButton.disabled = false;
        scannerActive = false;
    }

    // Manejar código escaneado
    function handleScannedCode(code) {
        stopScanner();
        
        resultDiv.textContent = `Código escaneado: ${code}`;
        resultDiv.className = 'success';
        
        if (scannerOverlay) scannerOverlay.style.display = 'none';
        
        scannedCodeInput.value = code;
        scanForm.style.display = 'block';
    }

    // Inicializar
    setupTypeSelector();
    startButton.addEventListener('click', initScanner);
});