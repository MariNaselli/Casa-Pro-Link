// 1. GESTIÓN DE MODAL ELIMINAR
function prepararEliminar(url) {
    const btn = document.getElementById("btnConfirmarEliminar");
    if (btn) btn.setAttribute("href", url);
}

// 2. COMPARTIR EN WHATSAPP (Genérico para Index y Ficha)
function compartirWhatsApp(titulo, id) {
    const urlFicha = window.location.origin + "/propiedad/" + id;
    const mensaje = `🏠 *PROPIEDAD DISPONIBLE*\n📍 *${titulo}*\n\n🔗 *Ver fotos y detalles aquí:* ${urlFicha}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(mensaje)}`, "_blank");
}

// 3. COPIAR LINK AL PORTAPAPELES
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

// 4. TOGGLE INMOBILIARIA (Solo Admin)
function actualizarEstadoInmo(id) {
    const check = document.getElementById("checkInmo");
    const seccion = document.getElementById("seccionInmo");
    
    if (seccion) seccion.style.display = check.checked ? "block" : "none";
    
    fetch(`/toggle_inmo/${id}`, { method: "POST" })
        .then(res => res.json())
        .then(data => console.log("Estado inmo actualizado:", data.nuevo_estado));
}