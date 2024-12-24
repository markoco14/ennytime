document.addEventListener('DOMContentLoaded', () => {
    const closeModalButton = document.querySelector('.js-christmas-modal-button');
    const christmasModalOverlay = document.querySelector('.js-christmas-overlay');
    const christmasModal = document.querySelector('.js-christmas-modal');

    if (!christmasModalOverlay || !christmasModal) {
        return;
    }

    // show the modal
    christmasModalOverlay.classList.remove('opacity-0');
    christmasModal.classList.remove('translate-y-16');
    christmasModal.classList.remove('opacity-0');

    // hide the modal with button click
    if (!closeModalButton) {
        return;
    }

    closeModalButton.addEventListener('click', () => {
        christmasModalOverlay.classList.add('opacity-0');
        christmasModal.classList.add('translate-y-16');
        christmasModal.classList.add('opacity-0');
        setTimeout(() => {
            christmasModalOverlay.classList.add('hidden');
        }, 500);
    });
});
