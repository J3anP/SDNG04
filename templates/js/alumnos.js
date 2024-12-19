let body = document.body;
let sideBar = document.querySelector('.side-bar');

// Abrir el sidebar al hacer clic en el menú
document.querySelector('#menu-btn').onclick = () => {
   sideBar.classList.toggle('active');
   body.classList.toggle('active');
};

// Cerrar el sidebar al hacer clic en el botón de cerrar
document.querySelector('#close-btn').onclick = () => {
   sideBar.classList.remove('active');
   body.classList.remove('active');
};

// Cerrar el sidebar al hacer scroll si la pantalla es pequeña
window.onscroll = () => {
   if (window.innerWidth < 1200) {
      sideBar.classList.remove('active');
      body.classList.remove('active');
   }
};
