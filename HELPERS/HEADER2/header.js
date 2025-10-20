const burger = document.querySelector(".checkbox1");
const nav = document.querySelector(".header-nav");
const ul = document.querySelector(".header-nav ul");
const headerLI = document.querySelectorAll(".headerLI");
const body = document.body;

burger.addEventListener("click", () => {
  burger.classList.toggle("active");
  nav.classList.toggle("active");
  ul.classList.toggle("active");
  body.classList.toggle("stopScroll");
  headerLI.forEach((el) => {
    el.classList.toggle("active");
  });
});

headerLI.forEach((el) => {
  el.addEventListener("click", () => {
    nav.classList.remove("active");
    ul.classList.remove("active");
    body.classList.remove("stopScroll");
    headerLI.forEach((el) => {
      el.classList.remove("active");
    });
  });
});
