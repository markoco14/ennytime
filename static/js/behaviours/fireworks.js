document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.js-nye-fireworks')
    if (!container) {
        return
    }
    const fireworks = new Fireworks.default(container, {
        autoresize: true,
        rocketsPoint: {
            min: 30,
            max: 70
        }
    })
    fireworks.start()
});