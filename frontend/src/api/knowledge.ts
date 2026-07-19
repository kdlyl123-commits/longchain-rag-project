import client from "./client";

export const knowledgeApi = {
  getDocuments: (page: number, pageSize: number) =>
    client.get("/knowledge/documents", { params: { page, page_size: pageSize } }),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post("/knowledge/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteDocument: (id: number) =>
    client.delete(`/knowledge/documents/${id}`),
  getChunks: (docId: number) =>
    client.get(`/knowledge/documents/${docId}/chunks`),
  reprocessDocument: (id: number) =>
    client.post(`/knowledge/documents/${id}/reprocess`),
  getStats: () => client.get("/knowledge/stats"),
};
