import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Dropdown, theme } from "antd";
import {
  MessageOutlined,
  DatabaseOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuthStore } from "../stores/authStore";
import type { MenuProps } from "antd";

const { Header, Content } = AntLayout;

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isAdmin } = useAuthStore();
  const { token: themeToken } = theme.useToken();

  const selectedKey = location.pathname.startsWith("/admin")
    ? "/admin/knowledge"
    : "/chat";

  const menuItems: MenuProps["items"] = [
    {
      key: "/chat",
      icon: <MessageOutlined />,
      label: "问答",
    },
    ...(isAdmin()
      ? [
          {
            key: "/admin/knowledge",
            icon: <DatabaseOutlined />,
            label: "知识库管理",
          },
        ]
      : []),
  ];

  const userMenuItems: MenuProps["items"] = [
    {
      key: "profile",
      icon: <SettingOutlined />,
      label: "个人中心",
    },
    { type: "divider" },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      danger: true,
    },
  ];

  const handleUserMenuClick: MenuProps["onClick"] = ({ key }) => {
    if (key === "profile") {
      navigate("/profile");
    } else if (key === "logout") {
      logout();
      navigate("/login");
    }
  };

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: themeToken.colorBgContainer,
          borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
          paddingInline: 24,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <h1
            style={{
              margin: 0,
              fontSize: 18,
              fontWeight: 700,
              color: themeToken.colorPrimary,
              cursor: "pointer",
            }}
            onClick={() => navigate("/chat")}
          >
            📚 RAG 知识库问答
          </h1>
          <Menu
            mode="horizontal"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ border: "none", flex: 1 }}
          />
        </div>

        <Dropdown
          menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
          placement="bottomRight"
        >
          <Button type="text" icon={<UserOutlined />}>
            {user?.username}
            {isAdmin() && (
              <span
                style={{
                  fontSize: 11,
                  color: themeToken.colorPrimary,
                  marginLeft: 4,
                }}
              >
                管理员
              </span>
            )}
          </Button>
        </Dropdown>
      </Header>

      <Content>
        <Outlet />
      </Content>
    </AntLayout>
  );
}
