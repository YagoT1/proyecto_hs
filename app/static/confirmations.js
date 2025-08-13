// confirmations.js
function showConfirmationModal(message, callback) {
    if (confirm(message)) {
        callback(true);
    } else {
        callback(false);
    }
}

function showAdminToggleConfirmation(toggleUrl, actionType) {
    let message = '';
    switch(actionType) {
        case 'quitar_admin':
            message = '¿Estás seguro de que quieres QUITAR los permisos de ADMINISTRADOR a este usuario?';
            break;
        case 'hacer_admin':
            message = '¿Estás seguro de que quieres HACER ADMINISTRADOR a este usuario?';
            break;
        case 'quitar_moderator':
            message = '¿Estás seguro de que quieres QUITAR los permisos de MODERADOR a este usuario?';
            break;
        case 'hacer_moderator':
            message = '¿Estás seguro de que quieres HACER MODERADOR a este usuario?';
            break;
        case 'eliminar_usuario':
            message = '¿Estás seguro de que quieres ELIMINAR este usuario y TODOS sus registros? Esta acción es IRREVERSIBLE.';
            break;
        default:
            message = '¿Estás seguro de continuar con esta acción?';
    }

    showConfirmationModal(message, function(confirmed) {
        if (confirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = toggleUrl;
            document.body.appendChild(form);
            form.submit();
        }
    });
}
