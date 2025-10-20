const tocSwiper = new Swiper(".toc-swiper", {
  slidesPerView: "auto",
  spaceBetween: 24,
  grabCursor: true,
  freeMode: true,
  slidesOffsetAfter: 24,
  slidesOffsetBefore: 24,
  scrollbar: {
    el: ".swiper-scrollbar",
    draggable: true,
    snapOnRelease: false,
    dragSize: 206,
  },
  breakpoints: {
    750: {
      slidesOffsetAfter: 0,
      slidesOffsetBefore: 0,
    },
  },
});
