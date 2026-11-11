import { useEffect, useState } from "react";
import { api } from "../api";

export default function Sent({ campaignId }: { campaignId: number }) {
  const [stats, setStats] = useState<any>({});
  const [replies, setReplies] = useState<any[]>([]);
  const [prospects, setProspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [msg, setMsg] = useState("");
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, r, p] = await Promise.all([
        api.stats(campaignId),
        api.replies(campaignId),
        api.listProspects(campaignId),
      ]);
      setStats(s);
      setReplies(r);
      setProspects(p);
    } catch (err: any) {
      setMsg("Lỗi tải dữ liệu: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campaignId]);

  const handleSendApproved = async (simulate: boolean = false) => {
    setSending(true);
    setMsg("");
    try {
      const results = simulate
        ? await api.simulateSend(campaignId)
        : await api.sendCampaign(campaignId);
      await loadData();
      const sentCount = results.filter((r: any) => r.status === "sent").length;
      const blockedCount = results.filter((r: any) => r.status === "blocked").length;
      const failedCount = results.filter((r: any) => r.status === "failed").length;

      let report = simulate ? "⚡ [Demo Mode] " : "";
      report += `Kết quả gửi: ${sentCount} thành công`;
      if (blockedCount > 0) report += `, ${blockedCount} bị chặn (an toàn chống trùng / giới hạn gửi)`;
      if (failedCount > 0) report += `, ${failedCount} lỗi`;
      setMsg(report);
    } catch (err: any) {
      setMsg("Lỗi khi gửi tin nhắn: " + err.message);
    } finally {
      setSending(false);
    }
  };

  const handleSyncReplies = async () => {
    setSyncing(true);
    setMsg("");
    try {
      const res = await api.syncReplies(campaignId);
      await loadData();
      setMsg(res.message || `Đã đồng bộ ${res.synced_count} phản hồi mới.`);
    } catch (err: any) {
      setMsg("Lỗi đồng bộ phản hồi: " + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const handleSimulateReplies = async () => {
    setSyncing(true);
    setMsg("");
    try {
      const res = await api.simulateReplies(campaignId);
      await loadData();
      setMsg(res.message || "Đã mô phỏng phản hồi từ ứng viên!");
    } catch (err: any) {
      setMsg("Lỗi mô phỏng: " + err.message);
    } finally {
      setSyncing(false);
    }
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const sentList = prospects.filter((p) => p.sent_status);
  const approvedWaiting = prospects.filter((p) => p.draft_status === "approved" && !p.sent_status);

  return (
    <div className="space-y-6">
      {/* Top Banner & Main Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
          <div>
            <h3 className="font-bold text-lg text-gray-900">
              Bảng điều khiển Outreach & Theo dõi Hội thoại
            </h3>
            <p className="text-xs text-gray-500">
              Kiểm soát quy tắc nền tảng X: cooldown, giới hạn ngày, không bao giờ gửi trùng một người.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleSendApproved(true)}
              disabled={sending || approvedWaiting.length === 0}
              className="bg-amber-600 hover:bg-amber-700 text-white text-xs px-3.5 py-2 rounded-lg font-medium shadow-sm transition disabled:opacity-50 flex items-center gap-1.5"
              title="Mô phỏng gửi an toàn dành cho tài khoản X Free Tier"
            >
              {sending ? "Đang gửi..." : `⚡ Gửi mô phỏng (${approvedWaiting.length})`}
            </button>
            <button
              onClick={() => handleSendApproved(false)}
              disabled={sending || approvedWaiting.length === 0}
              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-4 py-2 rounded-lg font-medium shadow transition disabled:opacity-50 flex items-center gap-1.5"
            >
              {sending ? "Đang gửi an toàn..." : `🚀 Gửi qua X API (${approvedWaiting.length})`}
            </button>
            <button
              onClick={handleSyncReplies}
              disabled={syncing}
              className="bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs px-3.5 py-2 rounded-lg font-medium transition flex items-center gap-1.5"
            >
              {syncing ? "Đang kiểm tra..." : "🔄 Kiểm tra tin nhắn X"}
            </button>
            <button
              onClick={handleSimulateReplies}
              disabled={syncing}
              className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs px-3.5 py-2 rounded-lg font-medium transition flex items-center gap-1.5"
            >
              ⚡ Mô phỏng phản hồi (Demo)
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <Stat title="Tổng ứng viên" value={stats.total_prospects ?? "—"} />
          <Stat
            title="Đã duyệt chờ gửi"
            value={stats.approved_drafts ?? approvedWaiting.length}
            className="border-indigo-100 bg-indigo-50/30 text-indigo-700"
          />
          <Stat
            title="Đã gửi thành công"
            value={stats.sent ?? "—"}
            className="border-emerald-100 bg-emerald-50/30 text-emerald-700"
          />
          <Stat
            title="Thất bại / Chặn"
            value={stats.failed ?? "—"}
            className="border-red-100 bg-red-50/30 text-red-600"
          />
          <Stat
            title="Đã trả lời"
            value={stats.responded ?? "—"}
            className="border-blue-100 bg-blue-50/30 text-blue-700"
          />
          <Stat
            title="Cần chú ý"
            value={stats.needs_attention ?? "—"}
            className="border-amber-200 bg-amber-50 text-amber-700 font-bold"
          />
        </div>

        {msg && (
          <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 text-indigo-900 rounded-lg text-sm">
            {msg}
          </div>
        )}
      </div>

      {/* Inbound Replies (Needs Attention) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-lg text-gray-900">
              Hộp thư phản hồi & Cần chú ý ({replies.length})
            </h3>
            <p className="text-xs text-gray-500">
              Các cuộc trò chuyện thực tế bắt đầu từ chiến dịch outreach của GenAI Fund.
            </p>
          </div>
          <button
            onClick={handleSimulateReplies}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
          >
            + Tạo thêm phản hồi thử nghiệm
          </button>
        </div>

        {replies.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm bg-gray-50/50 rounded-lg border border-dashed border-gray-200">
            Chưa có phản hồi mới. Bấm <b>"⚡ Mô phỏng phản hồi (Demo)"</b> ở trên để xem cách hộp thư hoạt động!
          </div>
        ) : (
          <div className="space-y-3">
            {replies.map((r) => (
              <div
                key={r.id}
                className="border border-amber-200 bg-amber-50/40 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-amber-900">
                      {r.display_name || `@${r.username}`}
                    </span>
                    <a
                      href={`https://x.com/${r.username}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      @{r.username}
                    </a>
                    {r.needs_attention && (
                      <span className="text-[10px] bg-amber-200 text-amber-900 px-2 py-0.5 rounded font-bold">
                        ◐ CẦN TRẢ LỜI
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-800 bg-white p-2.5 rounded border border-amber-100">
                    "{r.content_snippet || "—"}"
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1">Nhận lúc: {r.occurred_at}</div>
                </div>

                <a
                  href={`https://x.com/messages`}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3.5 py-2 rounded-lg font-medium transition self-start md:self-center whitespace-nowrap"
                >
                  Mở hộp thư X để trả lời →
                </a>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Outbound Sent Messages */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="font-bold text-lg text-gray-900 mb-1">
          Nhật ký Tin nhắn đã gửi ({sentList.length})
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Hệ thống lưu vết từng tin nhắn, đảm bảo 100% không bao giờ gửi trùng cho cùng một người.
        </p>

        {sentList.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-sm">
            Chưa có tin nhắn nào được gửi trong chiến dịch này. Hãy duyệt nháp rồi bấm "Gửi mô phỏng" hoặc "Gửi qua X API".
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200 text-xs uppercase tracking-wider">
                  <th className="pb-3 pr-4">Ứng viên</th>
                  <th className="pb-3 pr-4">Nội dung DM đã gửi</th>
                  <th className="pb-3 pr-4">Trạng thái</th>
                  <th className="pb-3 pr-4">X DM ID / Chi tiết</th>
                  <th className="pb-3 text-right">Dự phòng</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sentList.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 transition">
                    <td className="py-3 pr-4">
                      <div className="font-semibold text-gray-900">{p.display_name || p.username}</div>
                      <a
                        href={`https://x.com/${p.username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        @{p.username}
                      </a>
                    </td>
                    <td className="py-3 pr-4 max-w-[280px]">
                      <div className="text-xs text-gray-700 line-clamp-2">{p.draft_text || "—"}</div>
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`inline-block text-[10px] px-2.5 py-1 rounded-full font-bold uppercase ${
                          p.sent_status === "sent"
                            ? "bg-emerald-100 text-emerald-800"
                            : p.sent_status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {p.sent_status === "sent"
                          ? "Đã gửi"
                          : p.sent_status === "failed"
                          ? "Thất bại"
                          : "Bị chặn"}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-xs text-gray-500 max-w-[200px] truncate">
                      {p.x_dm_id ? `ID: ${p.x_dm_id}` : p.sent_error || "—"}
                    </td>
                    <td className="py-3 text-right">
                      {p.draft_text && (
                        <button
                          onClick={() => copyToClipboard(p.draft_text, p.id)}
                          className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2.5 py-1 rounded transition"
                        >
                          {copiedId === p.id ? "✓ Đã chép" : "Sao chép DM"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ title, value, className }: { title: string; value: any; className?: string }) {
  return (
    <div className={`p-4 rounded-xl border ${className || "border-gray-200 bg-white"}`}>
      <div className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold mb-1">{title}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
