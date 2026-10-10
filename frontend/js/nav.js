// Actualiza la navegacion segun si hay sesion iniciada y arma logout.
function renderNav(activePage) {
  const nav = document.getElementById("site-nav");
  if (!nav) return;

  const links = [
    { href: "index.html", label: "Catálogo", page: "catalogo" },
    { href: "cart.html", label: "Carrito", page: "carrito" },
    { href: "orders.html", label: "Mis pedidos", page: "pedidos" },
  ];

  nav.innerHTML = "";
  links.forEach((l) => {
    const a = document.createElement("a");
    a.href = l.href;
    a.textContent = l.label;
    if (l.page === activePage) a.classList.add("active");
    nav.appendChild(a);
  });

  const authLink = document.createElement("a");
  if (isLoggedIn()) {
    authLink.href = "#";
    authLink.textContent = "Cerrar sesión";
    authLink.addEventListener("click", (e) => {
      e.preventDefault();
      clearToken();
      window.location.href = "index.html";
    });
  } else {
    authLink.href = "login.html";
    authLink.textContent = "Ingresar";
    if (activePage === "login") authLink.classList.add("active");
  }
  nav.appendChild(authLink);

  // El link "Panel admin" depende del rol del usuario logueado, asi que
  // se agrega despues de una consulta async (no bloquea el resto del
  // nav, que ya quedo renderizado arriba).
  if (isLoggedIn()) {
    Api.me()
      .then((user) => {
        if (user.role !== "admin") return;
        const adminLink = document.createElement("a");
        adminLink.href = "admin.html";
        adminLink.textContent = "Panel admin";
        if (activePage === "admin") adminLink.classList.add("active");
        nav.insertBefore(adminLink, authLink);
      })
      .catch(() => {
        /* si el token vencio, apiFetch ya lo limpio; no hacemos nada mas */
      });
  }
}

// Muestra un modal avisando que hace falta iniciar sesion para acceder
// a la seccion actual. "message" es el texto especifico de la pagina
// (ej: "para ver tu carrito") y "backHref" es a donde va el boton
// "Volver" (por defecto el catalogo).
function showAuthRequiredModal(message, backHref = "index.html") {
  // Evita duplicar el modal si por algun motivo se llama dos veces.
  if (document.getElementById("auth-modal-overlay")) return;

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.id = "auth-modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box">
      <div class="modal-icon">🔒</div>
      <h2>Iniciá sesión para continuar</h2>
      <p>${message}</p>
      <div class="modal-actions">
        <button class="secondary" id="auth-modal-back">Volver</button>
        <button id="auth-modal-login">Iniciar sesión</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  document.getElementById("auth-modal-login").addEventListener("click", () => {
    window.location.href = "login.html";
  });
  document.getElementById("auth-modal-back").addEventListener("click", () => {
    window.location.href = backHref;
  });
  // Tambien se puede cerrar tocando fuera de la caja, y vuelve a la pagina indicada.
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) window.location.href = backHref;
  });
}
