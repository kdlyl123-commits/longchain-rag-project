import client from "./client";

export const chatApi = {
  getConversations: () => client.get("/chat/conversations"),
  createConversation: (title?: string) =>
    client.post("/chat/conversations", { title }),
  deleteConversation: (id: number) => client.delete(`/chat/conversations/${id}`),
  getMessages: (conversationId: number) =>
    client.get(`/chat/conversations/${conversationId}/messages`),
  sendMessage: (conversationId: number, content: string) =>
    fetch(`/api/chat/conversations/${conversationId}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({ content }),
    }),
};
