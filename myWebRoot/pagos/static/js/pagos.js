/*Función para mostrar notificaciones toast*/
function showToast(message, type = 'info') {
    // Crear elemento toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;
    
    // Agregar estilos inline para el toast
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#0066FF'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        opacity: 0;
        transform: translateX(100px);
        transition: all 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Mostrar toast
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Ocultar toast después de 3 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

/*Función para animar elementos cuando entran en vista*/
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            }
        });
    });
    
    elements.forEach(el => observer.observe(el));
}

// =====================================================
// MÉTODOS DE PAGO
// =====================================================

/*Funcionalidad para seleccionar métodos de pago*/
function initMetodosPago() {
    const metodoCards = document.querySelectorAll('.metodo-pago-card');
    const inputMetodoPago = document.getElementById('metodo_pago_seleccionado');
    const btnContinuar = document.querySelector('.btn-continuar');
    
    if (!metodoCards.length) return;
    
    metodoCards.forEach((card, index) => {
        // Agregar animación de entrada escalonada
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate-on-scroll');
        
        card.addEventListener('click', function() {
            // Remover selección anterior con animación
            metodoCards.forEach(c => {
                c.classList.remove('seleccionado');
                // Agregar efecto de deselección
                if (c !== this) {
                    c.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        c.style.transform = '';
                    }, 150);
                }
            });
            
            // Seleccionar este método con animación
            this.classList.add('seleccionado');
            this.style.transform = 'scale(1.05)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Actualizar input hidden
            if (inputMetodoPago) {
                inputMetodoPago.value = this.dataset.id;
            }
            
            // Animar y habilitar botón continuar
            if (btnContinuar) {
                btnContinuar.disabled = false;
                btnContinuar.style.animation = 'pulse 0.5s ease';
                setTimeout(() => {
                    btnContinuar.style.animation = '';
                }, 500);
            }
            
            // Mostrar notificación
            const metodoNombre = this.querySelector('.metodo-nombre').textContent;
            showToast(`Método seleccionado: ${metodoNombre}`, 'success');
        });
        
        // Efecto hover mejorado
        card.addEventListener('mouseenter', function() {
            if (!this.classList.contains('seleccionado')) {
                this.style.transform = 'translateY(-8px) scale(1.02)';
            }
        });
        
        card.addEventListener('mouseleave', function() {
            if (!this.classList.contains('seleccionado')) {
                this.style.transform = '';
            }
        });
    });
}

// =====================================================
// TRANSFERENCIA BANCARIA
// =====================================================

/*Funcionalidad para upload de comprobante*/
function initComprobanteUpload() {
    const inputComprobante = document.getElementById('input-comprobante');
    const btnExaminar = document.getElementById('btn-examinar');
    const archivoSeleccionado = document.getElementById('archivo-seleccionado');
    const uploadContainer = document.querySelector('.comprobante-upload');
    
    if (!inputComprobante || !btnExaminar || !archivoSeleccionado) return;
    
    // Click en botón examinar
    btnExaminar.addEventListener('click', function() {
        inputComprobante.click();
        
        // Efecto visual en el botón
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
            this.style.transform = '';
        }, 150);
    });
    
    // Cambio de archivo
    inputComprobante.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const fileName = file.name;
            const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
            
            // Validar tamaño (máximo 5MB)
            if (file.size > 5 * 1024 * 1024) {
                showToast('El archivo no debe superar los 5MB', 'error');
                this.value = '';
                return;
            }
            
            // Validar tipo de archivo
            const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
            if (!allowedTypes.includes(file.type)) {
                showToast('Solo se permiten archivos JPG, PNG o PDF', 'error');
                this.value = '';
                return;
            }
            
            // Mostrar información del archivo
            archivoSeleccionado.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px; color: #0066FF;">
                    <span>📎</span>
                    <div>
                        <div style="font-weight: 600;">${fileName}</div>
                        <div style="font-size: 0.8em; opacity: 0.7;">${fileSize} MB</div>
                    </div>
                </div>
            `;
            
            // Animar contenedor
            if (uploadContainer) {
                uploadContainer.style.borderColor = '#0066FF';
                uploadContainer.style.background = 'linear-gradient(135deg, #CCE5FF, #f5f9ff)';
            }
            
            showToast('Archivo seleccionado correctamente', 'success');
        } else {
            archivoSeleccionado.innerHTML = 'Ningún archivo seleccionado';
            archivoSeleccionado.style.color = '#666';
            
            if (uploadContainer) {
                uploadContainer.style.borderColor = '#ddd';
                uploadContainer.style.background = '';
            }
        }
    });
    
    // Drag and drop functionality
    if (uploadContainer) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            uploadContainer.style.borderColor = '#0066FF';
            uploadContainer.style.background = 'linear-gradient(135deg, #CCE5FF, #f5f9ff)';
            uploadContainer.style.transform = 'scale(1.02)';
        }
        
        function unhighlight(e) {
            uploadContainer.style.borderColor = '#ddd';
            uploadContainer.style.background = '';
            uploadContainer.style.transform = '';
        }
        
        uploadContainer.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                inputComprobante.files = files;
                inputComprobante.dispatchEvent(new Event('change'));
            }
        }
    }
}

/*Funcionalidad para copiar datos bancarios*/
function initCopiaDatosBancarios() {
    const datosValores = document.querySelectorAll('.datos-valor');
    
    datosValores.forEach(valor => {
        valor.style.cursor = 'pointer';
        valor.title = 'Click para copiar';
        
        valor.addEventListener('click', async function() {
            try {
                await navigator.clipboard.writeText(this.textContent.trim());
                
                // Efecto visual
                const originalBg = this.style.background;
                this.style.background = 'linear-gradient(135deg, #10b981, #34d399)';
                this.style.color = 'white';
                this.style.transform = 'scale(1.05)';
                
                setTimeout(() => {
                    this.style.background = originalBg;
                    this.style.color = '';
                    this.style.transform = '';
                }, 500);
                
                showToast('Copiado al portapapeles', 'success');
            } catch (err) {
                showToast('No se pudo copiar', 'error');
            }
        });
    });
}

// =====================================================
// PAGO MÓVIL
// =====================================================

/*Funcionalidad para validar número de teléfono*/
function initValidacionTelefono() {
    const inputTelefono = document.getElementById('numero_telefono');
    
    if (!inputTelefono) return;
    
    // Formatear número mientras se escribe
    inputTelefono.addEventListener('input', function() {
        let value = this.value.replace(/\D/g, ''); // Solo números
        
        // Limitar a 10 dígitos
        if (value.length > 10) {
            value = value.slice(0, 10);
        }
        
        // Formatear como XXX XXX XXXX
        if (value.length >= 6) {
            value = value.replace(/(\d{3})(\d{3})(\d{0,4})/, '$1 $2 $3');
        } else if (value.length >= 3) {
            value = value.replace(/(\d{3})(\d{0,3})/, '$1 $2');
        }
        
        this.value = value;
        
        // Validar longitud
        if (value.replace(/\s/g, '').length === 10) {
            this.style.borderColor = '#10b981';
            this.style.background = 'rgba(16, 185, 129, 0.1)';
        } else {
            this.style.borderColor = '#0066FF';
            this.style.background = '';
        }
    });
    
    // Validar al enviar formulario
    const form = inputTelefono.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const telefono = inputTelefono.value.replace(/\s/g, '');
            
            if (telefono.length !== 10) {
                e.preventDefault();
                inputTelefono.style.borderColor = '#ef4444';
                inputTelefono.style.background = 'rgba(239, 68, 68, 0.1)';
                showToast('Ingresa un número de teléfono válido (10 dígitos)', 'error');
                inputTelefono.focus();
                return false;
            }
            
            // Mostrar loading en el botón
            const btnSubmit = form.querySelector('button[type="submit"]');
            if (btnSubmit) {
                btnSubmit.innerHTML = '⏳ Procesando...';
                btnSubmit.disabled = true;
            }
        });
    }
}

/*Animación del código QR*/
function initAnimacionQR() {
    const qrCode = document.querySelector('.qr-code');
    
    if (!qrCode) return;
    
    // Efecto de pulso periódico
    setInterval(() => {
        qrCode.style.animation = 'pulse 2s ease';
        setTimeout(() => {
            qrCode.style.animation = '';
        }, 2000);
    }, 10000); // cada 10 segundos
}

// =====================================================
// CONFIRMACIÓN DE PAGO
// =====================================================

/*Animaciones para la página de confirmación*/
function initConfirmacionAnimaciones() {
    const confirmacionContainer = document.querySelector('.confirmacion-container');
    const iconoConfirmacion = document.querySelector('.icono-confirmacion');
    
    if (!confirmacionContainer) return;
    
    // Animar entrada del contenedor
    confirmacionContainer.style.opacity = '0';
    confirmacionContainer.style.transform = 'translateY(30px)';
    
    setTimeout(() => {
        confirmacionContainer.style.opacity = '1';
        confirmacionContainer.style.transform = 'translateY(0)';
        confirmacionContainer.style.transition = 'all 0.6s ease';
    }, 100);
    
    // Animar ícono de confirmación
    if (iconoConfirmacion) {
        setTimeout(() => {
            iconoConfirmacion.style.animation = 'checkmark 0.8s ease';
        }, 300);
    }
    
    // Animar detalles uno por uno
    const detalleItems = document.querySelectorAll('.detalle-item');
    detalleItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
            item.style.transition = 'all 0.4s ease';
        }, 600 + (index * 100));
    });
}

/*Funcionalidad para botones de acción en confirmación*/
function initBotonesConfirmacion() {
    const btnDescargar = document.querySelector('.btn-descargar-factura');
    const btnVerPedido = document.querySelector('.btn-ver-pedido');
    
    // Efecto en botón descargar factura
    if (btnDescargar) {
        btnDescargar.addEventListener('click', function() {
            this.innerHTML = '⏳ Descargando...';
            setTimeout(() => {
                this.innerHTML = '<span class="icon-download"></span> Descargar Factura';
                showToast('Factura descargada exitosamente', 'success');
            }, 1500);
        });
    }
    
    // Efecto en botón ver pedido
    if (btnVerPedido) {
        btnVerPedido.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        btnVerPedido.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    }
}

// =====================================================
// EFECTOS GENERALES
// =====================================================

/*Efecto de partículas de celebración*/
function createConfetti() {
    if (!document.querySelector('.confirmacion-container')) return;
    
    const colors = ['#0066FF', '#4D94FF', '#FFD700', '#10b981'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position: fixed;
            width: 10px;
            height: 10px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            left: ${Math.random() * 100}vw;
            top: -10px;
            z-index: 9999;
            border-radius: 50%;
            animation: confetti-fall 3s linear forwards;
        `;
        
        document.body.appendChild(confetti);
        
        setTimeout(() => {
            if (confetti.parentNode) {
                confetti.parentNode.removeChild(confetti);
            }
        }, 3000);
    }
}

/*Agregar estilos CSS dinámicos*/
function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes confetti-fall {
            to {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }
        
        .animate-on-scroll {
            opacity: 0;
            transform: translateY(30px);
        }
    `;
    document.head.appendChild(style);
}

// =====================================================
// INICIALIZACIÓN
// =====================================================

/*Función principal de inicialización*/
function initPagos() {
    // Agregar estilos dinámicos
    addDynamicStyles();
    
    // Inicializar funcionalidades según la página
    initMetodosPago();
    initComprobanteUpload();
    initCopiaDatosBancarios();
    initValidacionTelefono();
    initAnimacionQR();
    initConfirmacionAnimaciones();
    initBotonesConfirmacion();
    
    // Efectos generales
    animateOnScroll();
    
    // Confeti en página de confirmación
    if (document.querySelector('.confirmacion-container')) {
        setTimeout(createConfetti, 1000);
    }
    
    console.log('🎉 JavaScript de Pagos inicializado correctamente');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPagos);
} else {
    initPagos();
}