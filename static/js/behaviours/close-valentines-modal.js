document.addEventListener('DOMContentLoaded', () => {
    const closeValentinesModalButton = document.querySelector('.js-valentines-modal-button');
    const valentinesModalOverlay = document.querySelector('.js-valentines-overlay');
    const valentinesModal = document.querySelector('.js-valentines-modal');

    if (!valentinesModalOverlay || !valentinesModal) {
        return;
    }

    // show the modal
    valentinesModalOverlay.classList.remove('opacity-0');
    valentinesModal.classList.remove('translate-y-16');
    valentinesModal.classList.remove('opacity-0');

    // hide the modal with button click
    if (!closeValentinesModalButton) {
        return;
    }

    closeValentinesModalButton.addEventListener('click', () => {
        valentinesModalOverlay.classList.add('opacity-0');
        valentinesModal.classList.add('translate-y-16');
        valentinesModal.classList.add('opacity-0');
        setTimeout(() => {
            valentinesModalOverlay.classList.add('hidden');
            valentinesModalOverlay.classList.remove('stacked');
        }, 500);
    });
});
