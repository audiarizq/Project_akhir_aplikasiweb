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

const roomsFilter = document.querySelector('#rooms-filter-form');
const roomDetail = document.querySelector('#room-detail');
const roomCards = document.querySelectorAll('.all-room-card');
const fieldsFilter = document.querySelector('#fields-filter-form');
const courtCards = document.querySelectorAll('.court-option');
let fieldMap = null;
let fieldMapRequest = 0;

async function initializeFieldMap(court) {
  const mapElement = document.querySelector('#field-map');
  const statusElement = document.querySelector('#field-map-status');
  if (!mapElement || !statusElement || typeof L === 'undefined') return;

  fieldMapRequest += 1;
  const requestId = fieldMapRequest;
  if (fieldMap) {
    fieldMap.remove();
    fieldMap = null;
  }

  const showMap = (latitude, longitude, zoom, message) => {
    fieldMap = L.map(mapElement).setView([latitude, longitude], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(fieldMap);
    L.marker([latitude, longitude]).addTo(fieldMap).bindPopup(court.dataset.name).openPopup();
    statusElement.textContent = message;
    window.setTimeout(() => fieldMap && fieldMap.invalidateSize(), 0);
  };

  const latitude = Number(court.dataset.latitude);
  const longitude = Number(court.dataset.longitude);
  if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
    showMap(latitude, longitude, 16, 'Lokasi venue berdasarkan data koordinat.');
    return;
  }

  statusElement.textContent = 'Mencari lokasi venue di OpenStreetMap...';
  const venueQuery = `${court.dataset.name}, ${court.dataset.address || court.dataset.place}`;
  const search = async query => {
    const params = new URLSearchParams({
      format: 'jsonv2',
      limit: '1',
      q: query,
      'accept-language': 'id'
    });
    const response = await fetch(`https://nominatim.openstreetmap.org/search?${params}`);
    if (!response.ok) throw new Error('Gagal menghubungi layanan peta.');
    return response.json();
  };

  try {
    let results = await search(venueQuery);
    let approximate = false;
    if (!results.length) {
      results = await search(court.dataset.place);
      approximate = true;
    }
    if (requestId !== fieldMapRequest || !results.length) {
      if (!results.length) statusElement.textContent = 'Lokasi belum ditemukan. Silakan tambahkan alamat atau koordinat nanti.';
      return;
    }

    const result = results[0];
    showMap(Number(result.lat), Number(result.lon), approximate ? 11 : 15, approximate
      ? `Lokasi venue belum ditemukan secara spesifik. Menampilkan area ${court.dataset.place}.`
      : 'Lokasi ditemukan berdasarkan data OpenStreetMap.');
  } catch (error) {
    if (requestId === fieldMapRequest) {
      statusElement.textContent = 'Peta belum dapat dimuat. Silakan coba lagi nanti.';
    }
  }
}

function filterRooms() {
  const location = document.querySelector('#room-location').value.trim().toLowerCase();
  const level = document.querySelector('#room-level').value;
  const date = document.querySelector('#room-date').value;
  const cards = document.querySelectorAll('.all-room-card');
  let visible = 0;
  cards.forEach(card => {
    const matches = (!location || card.dataset.location.includes(location)) &&
      (!level || card.dataset.level === level) && (!date || card.dataset.date === date);
    card.hidden = !matches;
    if (matches) visible += 1;
  });
  document.querySelector('#room-count').textContent = `${visible} room tersedia`;
  document.querySelector('#rooms-empty').classList.toggle('visible', visible === 0);
}

roomsFilter.addEventListener('submit', event => {
  event.preventDefault();
  filterRooms();
});

roomCards.forEach(card => card.addEventListener('click', event => {
  if (!event.target.closest('a')) {
    window.location.hash = `#rooms/${encodeURIComponent(card.dataset.title)}`;
  }
}));

document.querySelector('#landing-search-form').addEventListener('submit', event => {
  event.preventDefault();
  window.location.hash = '#rooms';
});

fieldsFilter.addEventListener('submit', event => {
  event.preventDefault();
  const location = document.querySelector('#court-location').value.trim().toLowerCase();
  const cards = document.querySelectorAll('.court-option');
  let visible = 0;
  cards.forEach(card => {
    const matches = !location || card.dataset.location.includes(location);
    card.hidden = !matches;
    if (matches) visible += 1;
  });
  document.querySelector('#court-count').textContent = `${visible} lapangan tersedia`;
  document.querySelector('#fields-empty').classList.toggle('visible', visible === 0);
});

function updatePageFromHash() {
  const auth = window.location.hash === '#login';
  const roomHash = window.location.hash.match(/^#rooms(?:\/(.*))?$/);
  const rooms = Boolean(roomHash);
  const fieldHash = window.location.hash.match(/^#bikin-room(?:\/(.*))?$/);
  const fields = Boolean(fieldHash);
  const fieldName = fieldHash && fieldHash[1] ? decodeURIComponent(fieldHash[1]) : '';
  const selectedCourt = fieldName && [...courtCards].find(card => card.dataset.name === fieldName);
  const roomName = roomHash && roomHash[1] ? decodeURIComponent(roomHash[1]) : '';
  const selectedRoom = roomName && [...roomCards].find(card => card.dataset.title === roomName);
  document.body.classList.toggle('auth-mode', auth);
  document.body.classList.toggle('rooms-mode', rooms);
  document.body.classList.toggle('fields-mode', fields);
  document.body.classList.toggle('field-detail-mode', Boolean(selectedCourt));
  document.body.classList.toggle('room-detail-mode', Boolean(selectedRoom));
  if (selectedRoom) {
    roomDetail.innerHTML = `<div class="eyebrow">Detail room</div><h2>${selectedRoom.dataset.title}</h2><p class="room-detail-place">📍 ${selectedRoom.dataset.place}</p><div class="room-detail-info"><span>◷ ${selectedRoom.dataset.dateLabel}<small>${selectedRoom.dataset.time}</small></span><span>◉ Level ${selectedRoom.dataset.level}</span><strong>${selectedRoom.dataset.price}<small>/orang</small></strong></div><p>Room open play untuk pemain badminton yang ingin bermain bersama dengan level yang sesuai.</p><a class="button" href="#login">Gabung ke room <b>↗</b></a>`;
  } else {
    roomDetail.innerHTML = '';
  }
  const fieldDetail = document.querySelector('#field-detail');
  if (selectedCourt) {
    let courtDetails = [];
    try {
      courtDetails = JSON.parse(selectedCourt.dataset.courtDetails || '[]');
    } catch (error) {
      courtDetails = [];
    }
    const courtList = courtDetails.length
      ? `<ul class="court-detail-list">${courtDetails.map(court => `<li><div><strong>${court.name}</strong><span>${court.floor} · ${court.status}</span></div><b>${court.price}/jam</b></li>`).join('')}</ul>`
      : '<p class="court-detail-empty">Detail lapangan individual belum tersedia.</p>';
    const address = selectedCourt.dataset.address ? `<p class="field-detail-address">${selectedCourt.dataset.address}</p>` : '';
    const mapLink = selectedCourt.dataset.googleMaps ? `<a class="field-map-link" href="${selectedCourt.dataset.googleMaps}" target="_blank" rel="noopener">Buka di Google Maps ↗</a>` : '';
    const verification = selectedCourt.dataset.verification ? `<span class="field-verification">${selectedCourt.dataset.verification}</span>` : '';
    fieldDetail.innerHTML = `<div class="field-gallery"><div></div><div></div><div></div></div><div class="eyebrow">Detail lapangan</div><h2>${selectedCourt.dataset.name}</h2><p class="field-detail-location">📍 ${selectedCourt.dataset.place}</p>${address}${mapLink}${verification}<div class="field-map-wrap"><div id="field-map-status" class="field-map-status" role="status">Memuat lokasi venue...</div><div id="field-map" class="field-map"></div></div><div class="field-detail-grid"><div><h3>Deskripsi venue</h3><p>${selectedCourt.dataset.description}</p></div><div><h3>Harga sewa</h3><strong>${selectedCourt.dataset.price}<small>/jam</small></strong></div><div><h3>Jam operasional</h3><p>${selectedCourt.dataset.hours}</p></div><div><h3>Fasilitas</h3><p>${selectedCourt.dataset.facilities}</p></div></div><div class="field-courts"><h3>Pilih lapangan</h3>${courtList}</div><div class="field-booking"><div><h3>Pilih tanggal</h3><span>${selectedCourt.dataset.courts}</span></div><label>Pilih tanggal bermain<input type="date"></label><button class="button" type="button">Lanjut pilih jam <b>↗</b></button></div>`;
    initializeFieldMap(selectedCourt);
  } else {
    fieldMapRequest += 1;
    if (fieldMap) {
      fieldMap.remove();
      fieldMap = null;
    }
    fieldDetail.innerHTML = '';
  }
  if (rooms) {
    document.querySelector('#rooms').scrollIntoView({ behavior: 'auto', block: 'start' });
  } else if (fields) {
    document.querySelector('#bikin-room').scrollIntoView({ behavior: 'auto', block: 'start' });
  } else if (window.location.hash === '#beranda') {
    document.querySelector('#beranda').scrollIntoView({ behavior: 'auto', block: 'start' });
  }
}

window.addEventListener('hashchange', updatePageFromHash);
updatePageFromHash();
