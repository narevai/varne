// The tooltips of the charts are Vega's, and Vega shows them for a moving pointer. A
// finger does not move over a drawing, so tapping a bar shows nothing. A tap on a chart is
// passed on as the pointer being there, and a tap anywhere else puts the tooltip away.
(() => {
  const TAP_MS = 700;
  let start = null; // where the finger went down
  let tap = null; // a tap that is about to be a click

  const tooltip = () => document.getElementById("vg-tooltip-element");

  document.addEventListener(
    "touchstart",
    (event) => {
      const touch = event.touches[0];
      start = { x: touch.clientX, y: touch.clientY };
    },
    { passive: true },
  );

  document.addEventListener(
    "touchend",
    (event) => {
      const touch = event.changedTouches[0];
      // a finger that moved is scrolling, not tapping
      const moved = start && Math.hypot(touch.clientX - start.x, touch.clientY - start.y) > 10;
      tap = moved ? null : { x: touch.clientX, y: touch.clientY, at: performance.now() };
    },
    { passive: true },
  );

  // The click comes after the events the browser sends for a tap by itself, one of which
  // takes the tooltip of the bar that was tapped before away again.
  document.addEventListener(
    "click",
    () => {
      if (!tap || performance.now() - tap.at > TAP_MS) return;
      const { x, y } = tap;
      tap = null;

      const target = document.elementFromPoint(x, y);
      if (!target || !target.closest(".vega-embed")) {
        const element = tooltip();
        if (element) element.classList.remove("visible");
        return;
      }

      // Vega listens to the pointer, and a finger sends no `pointermove` over a drawing
      for (const type of ["pointerover", "pointermove"]) {
        target.dispatchEvent(
          new PointerEvent(type, {
            bubbles: true,
            cancelable: true,
            view: window,
            pointerType: "mouse",
            isPrimary: true,
            pointerId: 1,
            clientX: x,
            clientY: y,
          }),
        );
      }
    },
    true,
  );
})();
