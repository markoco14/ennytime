function displaySuccess(id) {
    const success = document.getElementById(`${id}`)
    success.classList.toggle('hidden')
    
    requestAnimationFrame(() => {
        success.classList.toggle('-translate-y-2')
        success.classList.toggle('opacity-0')
        success.classList.toggle('opacity-100')
    })
    setTimeout(() => {
        success.classList.toggle('opacity-100')
        success.classList.toggle('opacity-0')

        success.addEventListener('transitionend', () => {
            success.classList.toggle('hidden')
            success.classList.toggle('-translate-y-2')
        }, {once: true})
    }, 2000)
}