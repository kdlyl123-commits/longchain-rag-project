import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./stores/authStore";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import KnowledgeManage from "./pages/KnowledgeManage";
import Profile from "./pages/Profile";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  const { token } = useAuthStore();

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/chat" /> : <Login />}
      />
      <Route
        path="/register"
        element={token ? <Navigate to="/chat" /> : <Register />}
      />
      <Route path="/" element={<ProtectedRoute />}>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/chat" />} />
          <Route path="chat" element={<Chat />} />
          <Route path="chat/:conversationId" element={<Chat />} />
          <Route path="admin/knowledge" element={<KnowledgeManage />} />
          <Route path="profile" element={<Profile />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/chat" />} />
    </Routes>
  );
}

export default App;
