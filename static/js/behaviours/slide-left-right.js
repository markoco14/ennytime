function toggleEnterFromRight(attribute) {
    const calendar = document.querySelector(`[${attribute}]`);
    if (!calendar) return;
    if (calendar.classList.contains("enter-from-left")) {
        calendar.classList.remove("enter-from-left");
    }
    if (!calendar.classList.contains("enter-from-right")) {
        calendar.classList.add("enter-from-right");
    }
}

function toggleEnterFromLeft(attribute) {
    const calendar = document.querySelector(`[${attribute}]`);
    if (!calendar) return;
    if (calendar.classList.contains("enter-from-right")) {
        calendar.classList.remove("enter-from-right");
    }
    if (!calendar.classList.contains("enter-from-left")) {
        calendar.classList.add("enter-from-left");
    }
}

function cleanSlideInClasses(eventTarget) {
    if (eventTarget.classList.contains('enter-from-right')) {
        eventTarget.classList.remove('enter-from-right')
    }
    if (eventTarget.classList.contains('enter-from-left')) {
        eventTarget.classList.remove('enter-from-left')
    }
}

htmx.on('htmx:afterSwap', function(evt) {
    const eventTarget = evt.detail.target;
    cleanSlideInClasses(eventTarget)
});