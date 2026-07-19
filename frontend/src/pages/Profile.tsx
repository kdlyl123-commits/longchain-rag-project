import { useState } from "react";
import { Card, Form, Input, Button, Typography, Divider, message } from "antd";
import { useAuthStore } from "../stores/authStore";

const { Title } = Typography;

export default function Profile() {
  const [loading, setLoading] = useState(false);
  const { user, changePassword } = useAuthStore();

  const onFinish = async (values: {
    old_password: string;
    new_password: string;
  }) => {
    setLoading(true);
    try {
      await changePassword(values);
      message.success("密码修改成功，请重新登录");
      // 清除表单
    } catch {
      // 错误已在拦截器中处理
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", padding: "0 16px" }}>
      <Card>
        <Title level={4}>个人中心</Title>
        <div style={{ marginBottom: 24 }}>
          <p>
            <strong>用户名：</strong>
            {user?.username}
          </p>
          <p>
            <strong>邮箱：</strong>
            {user?.email || "未设置"}
          </p>
          <p>
            <strong>角色：</strong>
            {user?.role === "admin" ? "管理员" : "普通用户"}
          </p>
          <p>
            <strong>注册时间：</strong>
            {user?.created_at
              ? new Date(user.created_at).toLocaleString("zh-CN")
              : "-"}
          </p>
        </div>

        <Divider />

        <Title level={5}>修改密码</Title>
        <Form name="changePassword" onFinish={onFinish} layout="vertical">
          <Form.Item
            name="old_password"
            label="旧密码"
            rules={[{ required: true, message: "请输入旧密码" }]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: "请输入新密码" },
              { min: 6, message: "密码至少 6 个字符" },
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={["new_password"]}
            label="确认新密码"
            rules={[
              { required: true, message: "请确认新密码" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("new_password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("两次输入的密码不一致"));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
