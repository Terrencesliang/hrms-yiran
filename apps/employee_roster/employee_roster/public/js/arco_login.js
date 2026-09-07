(function () {
	function initCarousel(root) {
		if (!root || root.dataset.ready === "1") return;
		root.dataset.ready = "1";

		const slides = Array.from(root.querySelectorAll(".arco-login-slide"));
		const dots = Array.from(root.querySelectorAll(".arco-login-dots button"));
		if (slides.length < 2) return;

		let index = Math.max(
			0,
			slides.findIndex((slide) => slide.classList.contains("is-active"))
		);
		let timer = 0;

		function show(next) {
			index = ((next % slides.length) + slides.length) % slides.length;
			slides.forEach((slide, i) => {
				slide.classList.toggle("is-active", i === index);
			});
			dots.forEach((dot, i) => {
				dot.classList.toggle("is-active", i === index);
			});
		}

		function play() {
			stop();
			timer = window.setInterval(() => show(index + 1), 4500);
		}

		function stop() {
			if (timer) window.clearInterval(timer);
			timer = 0;
		}

		dots.forEach((dot) => {
			dot.addEventListener("click", () => {
				const i = Number(dot.getAttribute("data-slide") || 0);
				show(i);
				play();
			});
		});

		root.addEventListener("mouseenter", stop);
		root.addEventListener("mouseleave", play);
		play();
	}

	function boot() {
		document.body.classList.add("arco-login-page");
		document.querySelectorAll("[data-arco-login-carousel]").forEach(initCarousel);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
