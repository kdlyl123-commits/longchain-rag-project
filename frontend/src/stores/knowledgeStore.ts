import { create } from "zustand";
import type { Document, DocumentChunk, KnowledgeStats } from "../types";
import { knowledgeApi } from "../api/knowledge";

interface KnowledgeState {
  documents: Document[];
  total: number;
  page: number;
  pageSize: number;
  stats: KnowledgeStats | null;
  loading: boolean;

  fetchDocuments: (page?: number) => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (id: number) => Promise<void>;
  fetchChunks: (docId: number) => Promise<DocumentChunk[]>;
  reprocessDocument: (id: number) => Promise<void>;
  fetchStats: () => Promise<void>;
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  documents: [],
  total: 0,
  page: 1,
  pageSize: 10,
  stats: null,
  loading: false,

  fetchDocuments: async (page = 1) => {
    set({ loading: true });
    const res = await knowledgeApi.getDocuments(page, get().pageSize);
    set({
      documents: res.data.items,
      total: res.data.total,
      page: res.data.page,
      loading: false,
    });
  },

  uploadDocument: async (file: File) => {
    set({ loading: true });
    await knowledgeApi.uploadDocument(file);
    await get().fetchDocuments();
  },

  deleteDocument: async (id: number) => {
    await knowledgeApi.deleteDocument(id);
    await get().fetchDocuments();
  },

  fetchChunks: async (docId: number) => {
    const res = await knowledgeApi.getChunks(docId);
    return res.data;
  },

  reprocessDocument: async (id: number) => {
    await knowledgeApi.reprocessDocument(id);
    await get().fetchDocuments();
  },

  fetchStats: async () => {
    const res = await knowledgeApi.getStats();
    set({ stats: res.data });
  },
}));
