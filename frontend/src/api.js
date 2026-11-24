import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 12000,
  headers: { "Content-Type": "application/json" },
});

export const getDashboard = () => api.get("/api/dashboard/summary").then(r => r.data);
export const getInventory = () => api.get("/api/inventory/").then(r => r.data);
export const getEvents = () => api.get("/api/inventory/events").then(r => r.data);
export const getProducts = (params = {}) => api.get("/api/products/", { params }).then(r => r.data);
export const getBatches = (params = {}) => api.get("/api/batches/", { params }).then(r => r.data);
export const getShelves = (params = {}) => api.get("/api/shelves/", { params }).then(r => r.data);
export const getAlerts = (params = {}) => api.get("/api/alerts/", { params }).then(r => r.data);
export const receiveStock = payload => api.post("/api/inventory/receive", payload).then(r => r.data);
export const adjustStock = (id, payload) => api.post(`/api/inventory/${id}/adjust`, payload).then(r => r.data);
export const markAlertRead = id => api.patch(`/api/alerts/${id}/read`).then(r => r.data);
export const resolveAlert = id => api.patch(`/api/alerts/${id}/resolve`).then(r => r.data);
export const refreshAlerts = () => api.post("/api/alerts/refresh").then(r => r.data);
export const createProduct = payload => api.post("/api/products/", payload).then(r => r.data);
export const updateProduct = (id, payload) => api.put(`/api/products/${id}`, payload).then(r => r.data);
export const deactivateProduct = id => api.delete(`/api/products/${id}`).then(r => r.data);
export const createBatch = payload => api.post("/api/batches/", payload).then(r => r.data);
export const createShelf = payload => api.post("/api/shelves/", payload).then(r => r.data);
export const updateShelf = (id, payload) => api.put(`/api/shelves/${id}`, payload).then(r => r.data);
export const deactivateShelf = id => api.delete(`/api/shelves/${id}`).then(r => r.data);

export function errorMessage(error) {
  return error?.response?.data?.detail || error?.message || "An unexpected error occurred.";
}

export default api;
