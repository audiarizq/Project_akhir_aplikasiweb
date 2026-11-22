const header = document.querySelector('#header');
const menu = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav-links');
window.addEventListener('scroll', () => header.classList.toggle('scrolled', window.scrollY > 24));
menu.addEventListener('click', () => { const open = nav.classList.toggle('open'); menu.setAttribute('aria-expanded', open); });
document.querySelectorAll('.nav-links a').forEach(link => link.addEventListener('click', () => nav.classList.remove('open')));

const authTabs = document.querySelectorAll('[data-auth-tab]');
const loginForm = document.querySelector('#login-form');
const registerForm = document.querySelector('#register-form');
const authButtons = document.querySelectorAll('.auth-tab');

function showAuthTab(tab) {
  const registering = tab === 'register';
  loginForm.classList.toggle('hidden', registering);
  registerForm.classList.toggle('hidden', !registering);
  authButtons.forEach(button => button.classList.toggle('active', button.dataset.authTab === tab));
}

authTabs.forEach(button => button.addEventListener('click', () => showAuthTab(button.dataset.authTab)));
document.querySelector('#google-login').addEventListener('click', () => {
  alert('Login Google akan tersedia setelah Google OAuth dikonfigurasi.');
});

function updatePageFromHash() {
  document.body.classList.toggle('auth-mode', window.location.hash === '#login');
}

window.addEventListener('hashchange', updatePageFromHash);
updatePageFromHash();
