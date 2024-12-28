document.addEventListener('DOMContentLoaded', () => {
    const closeNYEModalButton = document.querySelector('.js-nye-modal-button');
    const NYEModalOverlay = document.querySelector('.js-nye-overlay');
    const NYEModal = document.querySelector('.js-nye-modal');

    if (!NYEModalOverlay || !NYEModal) {
        return;
    }

    // show the modal
    NYEModalOverlay.classList.remove('opacity-0');
    NYEModal.classList.remove('translate-y-16');
    NYEModal.classList.remove('opacity-0');

    // hide the modal with button click
    if (!closeNYEModalButton) {
        return;
    }

    closeNYEModalButton.addEventListener('click', () => {
        NYEModalOverlay.classList.add('opacity-0');
        NYEModal.classList.add('translate-y-16');
        NYEModal.classList.add('opacity-0');
        setTimeout(() => {
            NYEModalOverlay.classList.add('hidden');
        }, 500);
    });
});
