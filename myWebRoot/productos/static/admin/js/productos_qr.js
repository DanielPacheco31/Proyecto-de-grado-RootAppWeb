// JavaScript para funcionalidades QR en Admin de Productos

function mostrarQRModal(codigo, nombreProducto) {
    // Crear modal dinámico
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;
    
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(codigo)}`;
    const barcodeUrl = `https://barcodeapi.org/api/128/${encodeURIComponent(codigo)}`;
    
    modal.innerHTML = `
        <div style="
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            position: relative;
        ">
            <button onclick="cerrarModal()" style="
                position: absolute;
                top: 15px;
                right: 15px;
                background: #ff4444;
                color: white;
                border: none;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 16px;
            ">×</button>
            
            <h2 style="color: #0066FF; margin-bottom: 10px;">📱 Códigos para Producto</h2>
            <h3 style="color: #666; margin-bottom: 25px; font-size: 16px;">${nombreProducto}</h3>
            
            <!-- Código QR -->
            <div style="margin-bottom: 30px;">
                <h4 style="color: #333; margin-bottom: 15px;">Código QR</h4>
                <img src="${qrUrl}" style="
                    border: 3px solid #0066FF;
                    border-radius: 10px;
                    background: white;
                    padding: 10px;
                    margin-bottom: 15px;
                " alt="QR Code">
                <br>
                <a href="${qrUrl}" target="_blank" style="
                    background: #28a745;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    text-decoration: none;
                    margin: 0 5px;
                    font-size: 12px;
                ">📥 Descargar QR</a>
            </div>
            
            <!-- Código de Barras -->
            <div style="margin-bottom: 25px;">
                <h4 style="color: #333; margin-bottom: 15px;">Código de Barras</h4>
                <img src="${barcodeUrl}" style="
                    border: 2px solid #666;
                    border-radius: 5px;
                    background: white;
                    padding: 10px;
                    margin-bottom: 15px;
                    max-width: 100%;
                " alt="Barcode" onerror="this.style.display='none'">
                <br>
                <a href="${barcodeUrl}" target="_blank" style="
                    background: #6f42c1;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    text-decoration: none;
                    margin: 0 5px;
                    font-size: 12px;
                ">📊 Ver Código de Barras</a>
            </div>
            
            <!-- Código del producto -->
            <div style="
                background: #f0f0f0;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            ">
                <p style="margin: 0; color: #333;">
                    <strong>Código del Producto:</strong><br>
                    <span style="
                        font-family: monospace;
                        font-size: 20px;
                        font-weight: bold;
                        color: #0066FF;
                        background: white;
                        padding: 8px 15px;
                        border-radius: 5px;
                        display: inline-block;
                        margin-top: 8px;
                        border: 2px solid #0066FF;
                    ">${codigo}</span>
                </p>
            </div>
            
            <!-- Instrucciones -->
            <div style="
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                text-align: left;
            ">
                <p style="margin: 0 0 10px 0; color: #1976d2; font-weight: bold;">💡 Cómo usar estos códigos:</p>
                <ul style="margin: 0; padding-left: 20px; color: #666; font-size: 14px;">
                    <li>Descarga la imagen del QR</li>
                    <li>Ábrela en otra pantalla o imprímela</li>
                    <li>Usa tu app ROOT scanner para escanearla</li>
                    <li>El producto se agregará automáticamente al carrito</li>
                </ul>
            </div>
            
            <button onclick="cerrarModal()" style="
                background: #6c757d;
                color: white;
                border: none;
                padding: 12px 25px;
                margin-top: 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
            ">Cerrar</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Cerrar al hacer clic fuera
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            cerrarModal();
        }
    });
    
    // Cerrar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cerrarModal();
        }
    });
}

function cerrarModal() {
    const modals = document.querySelectorAll('div[style*="position: fixed"]');
    modals.forEach(modal => {
        if (modal.style.zIndex === '10000') {
            modal.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.remove();
                }
            }, 200);
        }
    });
}

// Agregar estilos de animación
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.9); }
    }
`;
document.head.appendChild(style);

console.log('📱 Sistema de códigos QR para productos cargado correctamente');