// sweet alert
document.addEventListener("htmx:confirm", function(evt) {
    // The event is triggered on every trigger for a request, so we need to check if the element
    // that triggered the request has a hx-confirm attribute, if not we can return early and let
    // the default behavior happen
    if (!evt.detail.target.hasAttribute('hx-confirm')) return

    // This will prevent the request from being issued to later manually issue it
    evt.preventDefault()

    // Hide your existing modal content
    const modal = document.getElementById('modal'); // Assuming your modal has this ID
    if (modal) {
        modal.classList.add('hidden'); // or any other way you want to hide the content
    }

    Swal.fire({
        title: "Remove from schedule",
        text: `${evt.detail.question}`,
        showCancelButton: true,
        customClass: {
            popup: 'w-[500px] aspect-square',
            confirmButton: 'flex justify-center items-center rounded bg-pink-500 text-white px-4 py-1',
            cancelButton: 'flex justify-center items-center rounded bg-gray-300 text-black px-4 py-1'
        },
        reverseButtons: true
    }).then(function(result) {
    if (result.isConfirmed) {
        if (modal) {
            modal.classList.remove('hidden');
        }

        // If the user confirms, we manually issue the request
        evt.detail.issueRequest(true); // true to skip the built-in window.confirm()

        // Remove the closest <li> element manually
        const liElement = evt.detail.target.closest('li');
        if (liElement.classList.contains('js-shift-li')) {
            liElement.classList.add('htmx-swapping')
            setTimeout(() => {
                liElement.remove();
            }, 700)
        }
    } else {
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    })
})