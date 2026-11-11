import { useEffect, useState } from "react";
import { api } from "../api";

export default function Connect({ onConnected }: { onConnected: (id: number) => void }) {
  const [step, setStep] = useState<"login" | "setup">("login");
  const [creds, setCreds] = useState({
    x_bearer_token: "",
    x_user_access_token: "",
    anthropic_api_key: "",
  });
  const [credStatus, setCredStatus] = useState<any>(null);
  const [campaignName, setCampaignName] = useState("AI & Robotics SEA Outreach");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [campaign, setCampaign] = useState<any>(null);

  useEffect(() => {
    // If token exists, check credentials status
    const token = localStorage.getItem("token");
    if (token) {
      setStep("setup");
      api.getCredentialsStatus()
        .then(setCredStatus)
        .catch(() => {});
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.login("admin", "admin");
      localStorage.setItem("token", res.access_token);
      setStep("setup");
      setMsg("");
      const st = await api.getCredentialsStatus();
      setCredStatus(st);
    } catch (err: any) {
      setMsg("Đăng nhập thất bại: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      // 1. Send provided credentials to runtime configuration
      if (creds.x_bearer_token || creds.x_user_access_token || creds.anthropic_api_key) {
        await api.updateCredentials(creds);
      }

      // 2. Create outreach campaign
      const res = await api.createCampaign({
        name: campaignName.trim() || "AI & Robotics SEA Outreach",
        segment_description: "AI/robotics builders, founders, researchers in Southeast Asia",
        max_sends_per_run: 25,
        max_sends_per_day: 100,
        cooldown_seconds: 90,
      });

      setCampaign(res);
      setMsg("Đã kết nối và tạo chiến dịch thành công.");
      setTimeout(() => {
        onConnected(res.id);
      }, 600);
    } catch (err: any) {
      setMsg("Lỗi thiết lập: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow border border-gray-200 p-8 max-w-lg mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <span className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></span>
        <h2 className="text-xl font-bold">Kết nối & Cấu hình Tài khoản Outreach</h2>
      </div>
      <p className="text-sm text-gray-600 mb-6">
        Dành riêng cho GenAI Fund. Kết nối tài khoản X của bạn để gửi DM tiếp cận cá nhân hóa không trùng lặp.
      </p>

      {step === "login" ? (
        <>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tài khoản quản trị</label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-gray-50"
                defaultValue="admin"
                readOnly
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-gray-50"
                defaultValue="admin"
                type="password"
                readOnly
              />
              <p className="text-xs text-gray-400 mt-1">Mặc định: admin / admin (đổi trong production)</p>
            </div>
            <button
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 rounded shadow disabled:opacity-50 transition"
              disabled={loading}
            >
              {loading ? "Đang xác thực..." : "Đăng nhập trang quản trị"}
            </button>
          </form>
          {msg && <p className="text-red-600 text-sm mt-3">{msg}</p>}
        </>
      ) : (
        <>
          {credStatus && (
            <div className="mb-5 p-3.5 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-1.5">
              <div className="font-semibold text-gray-700">Trạng thái API hiện tại:</div>
              <div className="flex items-center gap-2">
                <span className={credStatus.x_bearer_token_set ? "text-emerald-600 font-medium" : "text-amber-600"}>
                  {credStatus.x_bearer_token_set ? "✓ X Bearer Token: Đã kết nối" : "○ X Bearer Token: Chưa cấu hình"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={credStatus.x_user_access_token_set ? "text-emerald-600 font-medium" : "text-amber-600"}>
                  {credStatus.x_user_access_token_set ? "✓ X User Token (DM Write): Đã kết nối" : "○ X User Token: Chưa cấu hình (cần nếu gửi tự động)"}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={credStatus.anthropic_api_key_set ? "text-emerald-600 font-medium" : "text-indigo-600"}>
                  {credStatus.anthropic_api_key_set ? "✓ Anthropic Claude: Đã kết nối" : "○ Anthropic Claude: Chưa có (sẽ dùng bộ soạn nháp theo bằng chứng thực)"}
                </span>
              </div>
            </div>
          )}

          <form onSubmit={handleConnect} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tên chiến dịch</label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="VD: AI & Robotics SEA Outreach"
              />
            </div>

            <div className="border-t border-gray-200 pt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                X Bearer Token (App Read)
              </label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-indigo-500"
                type="password"
                value={creds.x_bearer_token}
                onChange={(e) => setCreds({ ...creds, x_bearer_token: e.target.value })}
                placeholder="Để trống nếu đã có trong .env"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                X User Access Token (DM Write & Read)
              </label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-indigo-500"
                type="password"
                value={creds.x_user_access_token}
                onChange={(e) => setCreds({ ...creds, x_user_access_token: e.target.value })}
                placeholder="OAuth user access token để gửi tin từ tài khoản X"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Anthropic API Key (Claude AI Drafting)
              </label>
              <input
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-indigo-500"
                type="password"
                value={creds.anthropic_api_key}
                onChange={(e) => setCreds({ ...creds, anthropic_api_key: e.target.value })}
                placeholder="sk-ant-... (tùy chọn; có fallback thông minh)"
              />
            </div>

            <button
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded shadow disabled:opacity-50 transition"
              disabled={loading}
            >
              {loading ? "Đang thiết lập chiến dịch..." : "Bắt đầu Chiến dịch Outreach"}
            </button>
          </form>

          {campaign && (
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
              Chiến dịch: <b>{campaign.name}</b> (ID: {campaign.id}) — Đang chuyển hướng...
            </div>
          )}
          {msg && <p className="text-sm mt-3 text-indigo-700 font-medium">{msg}</p>}
        </>
      )}
    </div>
  );
}
