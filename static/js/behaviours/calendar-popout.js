gsap.registerPlugin(Flip);

			function moveToModal(day_number) {
				const calendarCard = document.getElementById(
					`day-${day_number}`
				);
				const state = Flip.getState(calendarCard);

				const modal = document.getElementById("modal");
				const overlay = document.getElementById("overlay");
				modal.append(calendarCard);
				styleCalendarCard(day_number);
				showModal();
				Flip.from(state, {
					duration: 0.4,
					ease: "power1.inOut",
					absolute: true,
				})
			}

			function moveToCalendar(day_number) {
				const calendarCard = document.getElementById(
					`day-${day_number}`
				);
				const calendarContainer = document.getElementById(
					`container-${day_number}`
				);

				const state = Flip.getState(calendarCard);
				// Grab the current height of the calendar container
				const cardHeight = calendarCard.offsetHeight;
				const containerHeight = calendarContainer.offsetHeight;

				calendarCard.style.height = `${containerHeight}px`

				calendarContainer.append(calendarCard);
				styleCalendarCard(day_number);
				hideModal();
				Flip.from(state, {
					duration: 0.4,
					ease: "power1.inOut",
					absolute: true,
					onComplete: () => {
						// Reset the card's height after the animation completes
						calendarCard.style.height = '';
					}
				})
			}


			function showModal() {
				const overlay = htmx.find("#overlay");
				htmx.removeClass(overlay, "hidden");
				requestAnimationFrame(() => {
					htmx.removeClass(overlay, "opacity-0");
					htmx.addClass(overlay, "opacity-100");
				})
			}

			function hideModal() {
				const overlay = htmx.find("#overlay");
				htmx.removeClass(overlay, "opacity-100");
				htmx.addClass(overlay, "opacity-0");
				overlay.addEventListener('transitionend', () => {
					if (overlay.classList.contains("opacity-0")) {
						htmx.addClass(overlay, "hidden");
					}
				}, {once: true})
			}

			function styleCalendarCard(day_number) {
				let selectedCard = htmx.find(`#day-${day_number}`);
				htmx.toggleClass(selectedCard, "rounded-md", 400);
				htmx.toggleClass(selectedCard, "border", 400);

			}