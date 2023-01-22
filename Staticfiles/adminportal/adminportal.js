const accordion_buttons = document.querySelectorAll('.accordion-button');
accordion_buttons.forEach(i => {
  i.addEventListener('click', (e) => {
    const accordion_body = i.parentElement.parentElement.querySelector('.accordion-collapse');
    accordion_body.classList.toggle('show')
  })
});