// What is written on a segment of a bar is shown whole or not at all: where it would be
// cut short it is hidden, and it comes back when there is room. The segments come and go
// with the page and the bars change with its width, so this watches both.
(() => {
  let pending = 0;

  const fit = () => {
    document.querySelectorAll(".bar").forEach((bar) => {
      // on an ordered bar, nothing is shown to the right of what does not fit
      const ordered = bar.classList.contains("bar-ordered");
      let stopped = false;
      bar.querySelectorAll(":scope > .bar-seg > .seg-text").forEach((text) => {
        text.style.visibility = "visible";
        if (stopped) {
          text.style.visibility = "hidden";
        } else if (text.scrollWidth > text.clientWidth) {
          text.style.visibility = "hidden";
          if (ordered) stopped = true;
        }
      });
    });
  };

  const schedule = () => {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(fit);
  };

  window.addEventListener("resize", schedule);
  new ResizeObserver(schedule).observe(document.documentElement);
  new MutationObserver(schedule).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
