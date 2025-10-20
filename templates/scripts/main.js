document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("h1").forEach((p) => p.classList.add("defaultH1"));
});
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("h2").forEach((p) => p.classList.add("defaultH2"));
});
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("h3").forEach((p) => p.classList.add("defaultH3"));
});
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("h4").forEach((p) => p.classList.add("defaultH4"));
});
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("p").forEach((p) => p.classList.add("defaultP"));
});
const burger = document.querySelector(".ham");
const nav = document.querySelector(".nav");
const body = document.body;
const headerNavLink = document.querySelectorAll(".headerNavLink");

burger.addEventListener("click", () => {
  burger.classList.toggle("active");
  nav.classList.toggle("active");
  body.classList.toggle("stopScroll");
});

headerNavLink.forEach((el) => {
  el.addEventListener("click", () => {
    burger.classList.remove("active");
    nav.classList.remove("active");
    body.classList.remove("stopScroll");
  });
});
