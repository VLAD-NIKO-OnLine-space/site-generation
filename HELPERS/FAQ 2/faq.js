// const myAccordion = new gianniAccordion({
//   elements: ".card article",
//   trigger: "[data-accordion-element-trigger]",
//   content: "[data-accordion-element-content]",
//   oneAtATime: true,
// });

// const first = acc.els && acc.els[0];
// if (first) acc.open(first);

document.addEventListener("DOMContentLoaded", function () {
  const acc = new gianniAccordion({
    elements: ".card article", // поменяй на свой селектор
    oneAtATime: true, // как и было
  });

  acc.els.forEach(function (el) {
    el.content.addEventListener("click", function () {
      acc.toggle(el);
    });
  });

  // Открываем первый элемент вручную
  const first = acc.els && acc.els[0];
  if (first) acc.open(first);
});
