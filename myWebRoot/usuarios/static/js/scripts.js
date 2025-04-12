document.addEventListener('DOMContentLoaded', function() {
    // Inicializar todos los iconos de Lucide en la página
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    } else {
        console.error('La biblioteca Lucide no está disponible');
    }

    // Cambiar de panel al hacer clic en los elementos del menú
    const menuItems = document.querySelectorAll('.perfil-menu-item');
    const paneles = document.querySelectorAll('.perfil-panel');
    
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Eliminar clase activo de todos los elementos
            menuItems.forEach(i => i.classList.remove('activo'));
            paneles.forEach(p => p.classList.remove('activo'));
            
            // Añadir clase activo al elemento clickeado
            this.classList.add('activo');
            
            // Mostrar el panel correspondiente
            const targetId = this.getAttribute('data-target');
            document.getElementById(targetId).classList.add('activo');
        });
    });
    
    // Cambiar foto de perfil con validaciones
    const btnCambiarFoto = document.getElementById('cambiarFoto');
    const inputFoto = document.getElementById('inputFoto');
    const formFoto = document.getElementById('formFoto');
    
    if (btnCambiarFoto && inputFoto) {
        btnCambiarFoto.addEventListener('click', function() {
            inputFoto.click();
        });
        
        inputFoto.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validaciones de archivo
                const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
                const maxSize = 5 * 1024 * 1024; // 5MB
                
                if (!allowedTypes.includes(file.type)) {
                    alert('Solo se permiten imágenes JPG, PNG o GIF');
                    this.value = ''; // Limpiar selección
                    return;
                }
                
                if (file.size > maxSize) {
                    alert('La imagen no debe superar los 5MB');
                    this.value = ''; // Limpiar selección
                    return;
                }
                
                // Previsualizar imagen antes de subir (opcional)
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.querySelector('.perfil-foto').src = e.target.result;
                };
                reader.readAsDataURL(file);
                
                // Enviar formulario
                formFoto.submit();
            }
        });
    }
    
    // Validaciones de formularios
    const formInfoPersonal = document.querySelector('#info-personal form');
    const formSeguridad = document.querySelector('#seguridad form');
    
    if (formInfoPersonal) {
        formInfoPersonal.addEventListener('submit', function(e) {
            const email = document.getElementById('email');
            const telefono = document.getElementById('telefono');
            
            // Validación de email
            if (email && !email.value.includes('@')) {
                e.preventDefault();
                alert('Por favor, ingresa un correo electrónico válido');
                return;
            }
            
            // Validación opcional de teléfono (formato básico)
            if (telefono && telefono.value && !/^\+?[\d\s-]{7,15}$/.test(telefono.value)) {
                e.preventDefault();
                alert('Por favor, ingresa un número de teléfono válido');
                return;
            }
        });
    }
    
    if (formSeguridad) {
        formSeguridad.addEventListener('submit', function(e) {
            const newPassword1 = document.getElementById('new_password1');
            const newPassword2 = document.getElementById('new_password2');
            
            // Validación de contraseña
            if (newPassword1.value.length < 8) {
                e.preventDefault();
                alert('La contraseña debe tener al menos 8 caracteres');
                return;
            }
            
            if (newPassword1.value !== newPassword2.value) {
                e.preventDefault();
                alert('Las contraseñas no coinciden');
                return;
            }
        });
    }
});