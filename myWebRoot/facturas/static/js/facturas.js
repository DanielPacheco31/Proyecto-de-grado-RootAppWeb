/**
 * JavaScript para las funcionalidades de facturas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Animación de la barra de progreso
    animateProgressBar();
    
    // Inicializar tooltips (si existen)
    initTooltips();
    
    // Manejo de la confirmación de cancelación
    setupCancelConfirmation();
    
    // Botón para imprimir factura
    setupPrintButtons();
});

/**
 * Anima la barra de progreso del estado de la compra
 */
function animateProgressBar() {
    const progressBars = document.querySelectorAll('.linea-estado');
    
    if (!progressBars.length) return;
    
    // Aplicar animación con un pequeño retraso entre cada línea
    progressBars.forEach((bar, index) => {
        if (bar.classList.contains('activo')) {
            setTimeout(() => {
                bar.style.width = '100%';
            }, 300 * index);
        }
    });
}

/**
 * Inicializa tooltips para elementos con atributo data-tooltip
 */
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('data-tooltip');
            
            // Crear el tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            
            // Posicionar y añadir al DOM
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width/2) - (tooltip.offsetWidth/2)}px`;
            tooltip.style.opacity = '1';
            
            // Eliminar al salir el mouse
            this.addEventListener('mouseleave', function() {
                tooltip.remove();
            }, { once: true });
        });
    });
}

/**
 * Configura la confirmación para cancelar pedidos
 */
function setupCancelConfirmation() {
    const cancelForms = document.querySelectorAll('.form-cancelar');
    
    cancelForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (confirm('¿Estás seguro de que deseas cancelar esta compra? Esta acción no se puede deshacer.')) {
                this.submit();
            }
        });
    });
}

/**
 * Configura los botones para imprimir facturas
 */
function setupPrintButtons() {
    const printButtons = document.querySelectorAll('.btn-imprimir-factura');
    
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const facturaUrl = this.getAttribute('href');
            
            // Abrir en una nueva ventana y luego imprimir
            const printWindow = window.open(facturaUrl, '_blank');
            
            printWindow.addEventListener('load', function() {
                printWindow.print();
            });
        });
    });
}

/**
 * Función para mostrar un modal de confirmación personalizado
 * @param {string} message - Mensaje de confirmación
 * @param {Function} onConfirm - Función a ejecutar si se confirma
 * @param {Function} onCancel - Función a ejecutar si se cancela
 */
function showConfirmModal(message, onConfirm, onCancel) {
    // Comprobar si ya existe un modal
    let modal = document.querySelector('.confirm-modal');
    
    if (modal) {
        modal.remove();
    }
    
    // Crear el modal
    modal = document.createElement('div');
    modal.className = 'confirm-modal';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'confirm-modal-content';
    
    const messageEl = document.createElement('p');
    messageEl.textContent = message;
    
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'confirm-modal-buttons';
    
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = 'Confirmar';
    confirmBtn.className = 'btn-confirm';
    
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancelar';
    cancelBtn.className = 'btn-cancel';
    
    // Añadir eventos
    confirmBtn.addEventListener('click', function() {
        modal.remove();
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });
    
    cancelBtn.addEventListener('click', function() {
        modal.remove();
        if (typeof onCancel === 'function') {
            onCancel();
        }
    });
    
    // Ensamblar el modal
    buttonsContainer.appendChild(cancelBtn);
    buttonsContainer.appendChild(confirmBtn);
    
    modalContent.appendChild(messageEl);
    modalContent.appendChild(buttonsContainer);
    
    modal.appendChild(modalContent);
    
    // Añadir al DOM
    document.body.appendChild(modal);
    
    // Hacer que el modal sea visible con una animación
    setTimeout(() => {
        modal.style.opacity = '1';
        modalContent.style.transform = 'translateY(0)';
    }, 10);
    
    // También cerrar al hacer clic fuera
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.opacity = '0';
            modalContent.style.transform = 'translateY(-50px)';
            
            setTimeout(() => {
                modal.remove();
                if (typeof onCancel === 'function') {
                    onCancel();
                }
            }, 300);
        }
    });
}

// Estilos CSS adicionales para el modal (se añaden dinámicamente)
(function addModalStyles() {
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        .confirm-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .confirm-modal-content {
            background-color: white;
            border-radius: 8px;
            padding: 25px;
            min-width: 300px;
            max-width: 90%;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            transform: translateY(-50px);
            transition: transform 0.3s ease;
        }
        
        .confirm-modal p {
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 16px;
            color: #333;
        }
        
        .confirm-modal-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        .btn-cancel {
            background-color: #f5f5f5;
            color: #333;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .btn-cancel:hover {
            background-color: #e0e0e0;
        }
        
        .btn-confirm {
            background-color: #1877F2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .btn-confirm:hover {
            background-color: #0a5dc7;
        }
        
        .tooltip {
            position: absolute;
            background-color: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }
        
        .tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }
    `;
    
    document.head.appendChild(styleEl);
})();
/* scripts para cancelar factura */

function confirmarCancelacion() {
    // Confirmación personalizada
    if (confirm('¿Estás seguro de que deseas cancelar esta compra?\n\nEsta acción no se puede deshacer y:\n• Se cancelará la compra #{{ compra.id }}\n• Se restaurará el stock de los productos\n• No se realizará ningún pago')) {
        
        // Cambiar texto del botón mientras se procesa
        const btnCancelar = document.querySelector('.btn-cancelar');
        const textoOriginal = btnCancelar.textContent;
        btnCancelar.textContent = 'Cancelando...';
        btnCancelar.disabled = true;
        
        // Enviar formulario
        document.getElementById('formCancelar').submit();
    }
}
