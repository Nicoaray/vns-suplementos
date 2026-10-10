// Cliente de la API de VNS Suplementos.
// En local (http.server) apunta a localhost:8000. En cualquier otro
// dominio (por ejemplo el sitio estatico ya deployado en Render) apunta
// a la URL publica del backend: reemplazar por la URL real que te da
// Render despues del primer deploy (Dashboard -> servicio del backend
// -> URL arriba a la izquierda).
const API_BASE_URL =
  location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "https://vns-suplementos-backend.onrender.com";

const TOKEN_KEY = "vns_token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function isLoggedIn() {
  return !!getToken();
}

async function apiFetch(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {};
  const isFormData = options.body instanceof FormData;
  if (!(options.body instanceof URLSearchParams) && !isFormData) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    // Token vencido o invalido: limpiamos sesion.
    clearToken();
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = await res.json();
      detail = data.detail ? JSON.stringify(data.detail) : detail;
    } catch (_) {
      /* respuesta sin cuerpo JSON */
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

const Api = {
  // Auth
  register: (payload) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify(payload) }),

  login: async (email, password) => {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const data = await apiFetch("/auth/login", { method: "POST", body });
    setToken(data.access_token);
    return data;
  },

  me: () => apiFetch("/auth/me"),

  // Catalogo
  listCategories: () => apiFetch("/categories"),
  listProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/products${qs ? `?${qs}` : ""}`);
  },
  listFeatured: (limit = 10) => apiFetch(`/products/featured?limit=${limit}`),
  listNewArrivals: (limit = 10) => apiFetch(`/products/new?limit=${limit}`),
  listOnSale: (limit = 10) => apiFetch(`/products/on-sale?limit=${limit}`),

  // Carrito
  getCart: () => apiFetch("/cart"),
  addToCart: (product_id, quantity = 1) =>
    apiFetch("/cart/items", { method: "POST", body: JSON.stringify({ product_id, quantity }) }),
  updateCartItem: (itemId, quantity) =>
    apiFetch(`/cart/items/${itemId}`, { method: "PUT", body: JSON.stringify({ quantity }) }),
  removeCartItem: (itemId) => apiFetch(`/cart/items/${itemId}`, { method: "DELETE" }),

  // Ordenes
  createOrder: (shipping_address) =>
    apiFetch("/orders", { method: "POST", body: JSON.stringify({ shipping_address }) }),
  myOrders: () => apiFetch("/orders"),

  // --- Administracion (requieren rol admin) ---

  // Productos
  createProduct: (payload) => apiFetch("/products", { method: "POST", body: JSON.stringify(payload) }),
  updateProduct: (id, payload) => apiFetch(`/products/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteProduct: (id) => apiFetch(`/products/${id}`, { method: "DELETE" }),
  uploadProductImage: (id, file) => {
    const form = new FormData();
    form.append("file", file);
    return apiFetch(`/products/${id}/image`, { method: "POST", body: form });
  },
  // Trae todos los productos (activos e inactivos) para el panel de
  // administracion (el listado publico GET /products solo muestra
  // activos).
  listAllProductsForAdmin: () => apiFetch("/products/admin/all"),

  // Categorias
  createCategory: (payload) => apiFetch("/categories", { method: "POST", body: JSON.stringify(payload) }),
  updateCategory: (id, payload) => apiFetch(`/categories/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteCategory: (id) => apiFetch(`/categories/${id}`, { method: "DELETE" }),

  // Usuarios
  listUsers: () => apiFetch("/users"),
  updateUser: (id, payload) => apiFetch(`/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  // Pedidos
  listAllOrders: () => apiFetch("/orders/admin/all"),
  updateOrderStatus: (id, status) =>
    apiFetch(`/orders/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),

  // Estadisticas
  statsSummary: () => apiFetch("/admin/stats/summary"),
  statsSalesByDate: () => apiFetch("/admin/stats/sales-by-date"),
  statsTopProducts: (limit = 10) => apiFetch(`/admin/stats/top-products?limit=${limit}`),
};
