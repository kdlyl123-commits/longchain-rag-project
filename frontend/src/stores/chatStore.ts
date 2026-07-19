import { create } from "zustand";
import type { Conversation, Message } from "../types";
import { chatApi } from "../api/chat";

interface ChatState {
  conversations: Conversation[];
  currentConversationId: number | null;
  messages: Message[];
  streamingContent: string;
  citations: any[] | null;
  loading: boolean;
  streaming: boolean;

  fetchConversations: () => Promise<void>;
  createConversation: (title?: string) => Promise<Conversation>;
  deleteConversation: (id: number) => Promise<void>;
  fetchMessages: (conversationId: number) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setCurrentConversation: (id: number | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  streamingContent: "",
  citations: null,
  loading: false,
  streaming: false,

  fetchConversations: async () => {
    const res = await chatApi.getConversations();
    set({ conversations: res.data });
  },

  createConversation: async (title) => {
    const res = await chatApi.createConversation(title);
    const conv = res.data;
    set((s) => ({ conversations: [conv, ...s.conversations] }));
    return conv;
  },

  deleteConversation: async (id) => {
    await chatApi.deleteConversation(id);
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      ...(s.currentConversationId === id
        ? { currentConversationId: null, messages: [] }
        : {}),
    }));
  },

  fetchMessages: async (conversationId) => {
    const res = await chatApi.getMessages(conversationId);
    set({ messages: res.data, currentConversationId: conversationId });
  },

  sendMessage: async (content: string) => {
    const { currentConversationId } = get();
    if (!currentConversationId) return;

    set({ streaming: true, streamingContent: "", citations: null });

    // 添加用户消息到界面
    const userMsg: Message = {
      id: Date.now(),
      conversation_id: currentConversationId,
      role: "user",
      content,
      citations: null,
      created_at: new Date().toISOString(),
    };
    set((s) => ({ messages: [...s.messages, userMsg] }));

    try {
      const response = await chatApi.sendMessage(currentConversationId, content);

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let citations: any[] | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "content") {
                fullContent += parsed.content;
                set({ streamingContent: fullContent });
              } else if (parsed.type === "citations") {
                citations = parsed.citations;
                set({ citations });
              }
            } catch {
              // 纯文本（非 JSON 标准 SSE 格式）
              fullContent += data;
              set({ streamingContent: fullContent });
            }
          }
        }
      }

      // 添加 AI 回复到消息列表
      const assistantMsg: Message = {
        id: Date.now() + 1,
        conversation_id: currentConversationId,
        role: "assistant",
        content: fullContent,
        citations,
        created_at: new Date().toISOString(),
      };
      set((s) => ({
        messages: [...s.messages, assistantMsg],
        streamingContent: "",
        citations: null,
      }));

      // 刷新会话列表更新标题和时间
      get().fetchConversations();
    } catch (err) {
      set({ streamingContent: "", streaming: false });
      throw err;
    }

    set({ streaming: false });
  },

  setCurrentConversation: (id) => set({ currentConversationId: id }),
}));
