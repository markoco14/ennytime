document.addEventListener('DOMContentLoaded', () => {
    const valentinesOverlay = document.querySelector('.js-valentines-confetti')
    if (valentinesOverlay) {
        const defaults = {
            spread: 120,
            ticks: 100,
            gravity: 0,
            decay: 0.94,
            startVelocity: 30,
            shapes: ["heart"],
            colors: ["FFC0CB", "FF69B4", "FF1493", "C71585"],
          };
          
          confetti({
            ...defaults,
            particleCount: 150,
            scalar: 2,
            origin: {
                x: 0.5,
                y: 0.8,
            },
          });
          
          confetti({
            ...defaults,
            particleCount: 75,
            scalar: 3,
            origin: {
                x: 0.5,
                y: 0.8,
            },
          });
          
          confetti({
            ...defaults,
            particleCount: 40,
            scalar: 4,
            origin: {
                x: 0.5,
                y: 0.8,
            },
          });
    }
})