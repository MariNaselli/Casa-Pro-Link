// 1. GESTIÓN DE MODAL ELIMINAR
function prepararEliminar(url) {
    const btn = document.getElementById("btnConfirmarEliminar");
    if (btn) btn.setAttribute("href", url);
}

// 2. ACTUALIZAR VISUALIZACIÓN Y BASE DE DATOS (Switch Inmo)
function actualizarVisualizacionInmo(id) {
    const seccion = document.getElementById('seccionInmo');
    const switchInmo = document.getElementById('checkInmo');
    
    if (seccion && switchInmo) {
        if (switchInmo.checked) {
            seccion.classList.remove('d-none');
        } else {
            seccion.classList.add('d-none');
        }
    }
    // Guarda en la base de datos
    fetch(`/toggle_inmo/${id}`, { method: 'POST' });
}

// 3. COMPARTIR WHATSAPP (Lógica de Marca Blanca)
function compartirWhatsApp(titulo, id) {
    const checkInmo = document.getElementById("checkInmo");
    
    // Si el switch está marcado, incluimos la firma
    const mostrarInfoInmo = checkInmo ? checkInmo.checked : false;
    const urlFicha = window.location.origin + "/propiedad/" + id;
    
    let mensaje = `🏠 *PROPIEDAD DISPONIBLE*\n📍 *${titulo}*\n\n🔗 *Ver fotos y detalles aquí:* ${urlFicha}`;
    
    if (mostrarInfoInmo) {
        mensaje += `\n\n---\n🏢 *Inmobiliaria Hermano*\n📞 *Contacto:* 351-XXXXXXX`; 
    }

    window.open("https://wa.me/?text=" + encodeURIComponent(mensaje), "_blank");
}

// 4. COPIAR LINK AL PORTAPAPELES
function copiarLink() {
    const url = window.location.href;
    const btn = document.getElementById("btnCopiar");
    
    navigator.clipboard.writeText(url).then(() => {
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check2"></i> ¡Copiado!';
            btn.classList.replace("btn-outline-dark", "btn-success");
            
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.replace("btn-success", "btn-outline-dark");
            }, 2000);
        }
    });
}