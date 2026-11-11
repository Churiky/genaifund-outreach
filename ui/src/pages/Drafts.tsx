import { useEffect, useState } from "react";
import { api } from "../api";

interface DraftsProps {
  campaignId: number;
  onNavigateToSent?: () => void;
}

export default function Drafts({ campaignId, onNavigateToSent }: DraftsProps) {
  const [prospects, setProspects] = useState<any[]>([]);
  const [filter, setFilter] = useState<"pending" | "approved" | "all">("pending");
  const [editingDraftId, setEditingDraftId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const refresh = () => {
    api.listProspects(campaignId)
      .then(setProspects)
      .catch(() => setProspects([]));
  };

  useEffect(() => {
    refresh();
  }, [campaignId]);

  const handleEditStart = (p: any) => {
    setEditingDraftId(p.draft_id);
    setEditText(p.draft_text || "");
  };

  const handleEditSave = async (draftId: number) => {
    setLoading(true);
    try {
      await api.updateDraft(draftId, { dm_text: editText });
      setEditingDraftId(null);
      refresh();
      setMsg("Đã cập nhật nội dung nháp thành công.");
    } catch (err: any) {
      setMsg("Lỗi lưu nháp: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (draftId: number) => {
    setLoading(true);
    try {
      await api.approveDraft(draftId, "admin");
      refresh();
      setMsg("Đã phê duyệt nháp! Sẵn sàng để gửi.");
    } catch (err: any) {
      setMsg("Lỗi phê duyệt: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (draftId: number) => {
    setLoading(true);
    try {
      await api.rejectDraft(draftId);
      refresh();
      setMsg("Đã từ chối nháp.");
    } catch (err: any) {
      setMsg("Lỗi từ chối: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async (prospectId: number) => {
    setLoading(true);
    try {
      await api.createDraft(prospectId);
      refresh();
      setMsg("Đã soạn lại nháp từ bằng chứng mới nhất.");
    } catch (err: any) {
      setMsg("Lỗi soạn lại: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAll = async () => {
    setLoading(true);
    try {
      const pendingDrafts = prospects.filter((p) => p.draft_id && p.draft_status === "draft");
      for (const p of pendingDrafts) {
        await api.approveDraft(p.draft_id, "admin");
      }
      refresh();
      setMsg(`Đã phê duyệt toàn bộ ${pendingDrafts.length} nháp!`);
    } catch (err: any) {
      setMsg("Lỗi phê duyệt hàng loạt: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendApproved = async () => {
    setSending(true);
    setMsg("");
    try {
      const results = await api.sendCampaign(campaignId);
      refresh();
      const sentCount = results.filter((r: any) => r.status === "sent").length;
      const blockedCount = results.filter((r: any) => r.status === "blocked").length;
      const failedCount = results.filter((r: any) => r.status === "failed").length;

      let summary = `Kết quả gửi: ${sentCount} đã gửi thành công`;
      if (blockedCount > 0) summary += `, ${blockedCount} bị chặn (tránh trùng / quá giới hạn ngày)`;
      if (failedCount > 0) summary += `, ${failedCount} thất bại`;
      setMsg(summary);

      if (onNavigateToSent) {
        setTimeout(onNavigateToSent, 1500);
      }
    } catch (err: any) {
      setMsg("Lỗi thực hiện gửi: " + err.message);
    } finally {
      setSending(false);
    }
  };

  const displayedProspects = prospects.filter((p) => {
    if (!p.draft_id) return false;
    if (filter === "pending") return p.draft_status === "draft";
    if (filter === "approved") return p.draft_status === "approved";
    return true;
  });

  const approvedCount = prospects.filter((p) => p.draft_status === "approved").length;
  const pendingCount = prospects.filter((p) => p.draft_status === "draft").length;

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="font-bold text-lg text-gray-900">
              Soạn thảo, Xem xét & Phê duyệt Tin nhắn DM
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Mỗi tin nhắn đều dựa trên bằng chứng thực tế từ hồ sơ/bài viết của ứng viên. Không bịa đặt sự quen biết.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {pendingCount > 0 && (
              <button
                onClick={handleApproveAll}
                disabled={loading}
                className="bg-gray-100 hover:bg-gray-200 text-gray-800 text-xs px-3.5 py-2 rounded-lg font-medium transition"
              >
                ✓ Duyệt tất cả ({pendingCount})
              </button>
            )}
            {approvedCount > 0 && (
              <button
                onClick={handleSendApproved}
                disabled={sending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-4 py-2 rounded-lg font-medium shadow transition flex items-center gap-1.5"
              >
                {sending ? "Đang gửi an toàn..." : `🚀 Gửi ${approvedCount} tin nhắn đã duyệt`}
              </button>
            )}
          </div>
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 mt-5 border-t border-gray-100 pt-4">
          <button
            onClick={() => setFilter("pending")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              filter === "pending"
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Chờ phê duyệt ({pendingCount})
          </button>
          <button
            onClick={() => setFilter("approved")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              filter === "approved"
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Đã duyệt sẵn sàng gửi ({approvedCount})
          </button>
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              filter === "all"
                ? "bg-indigo-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Tất cả nháp ({prospects.filter((p) => p.draft_id).length})
          </button>
        </div>

        {msg && (
          <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 text-indigo-900 rounded-lg text-sm">
            {msg}
          </div>
        )}
      </div>

      {/* Drafts List */}
      <div className="space-y-4">
        {displayedProspects.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400 text-sm">
            Không có nháp nào trong mục này. Hãy chuyển sang trang "Tìm ứng viên" và nhấn "Soạn DM".
          </div>
        ) : (
          displayedProspects.map((p) => (
            <div
              key={p.id}
              className={`bg-white rounded-xl shadow-sm border p-5 transition ${
                p.draft_status === "approved"
                  ? "border-emerald-200 bg-emerald-50/20"
                  : p.draft_status === "failed"
                  ? "border-red-200 opacity-60"
                  : "border-gray-200"
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                    {(p.display_name || p.username || "U")[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{p.display_name || p.username}</div>
                    <div className="text-xs text-gray-500">
                      @{p.username} · Điểm phù hợp:{" "}
                      <span className="font-bold text-indigo-700">{p.fit_score}/100</span>
                    </div>
                  </div>
                </div>
                <span
                  className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wide ${
                    p.draft_status === "approved"
                      ? "bg-emerald-100 text-emerald-800"
                      : p.draft_status === "sent"
                      ? "bg-blue-100 text-blue-800"
                      : p.draft_status === "failed"
                      ? "bg-red-100 text-red-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {p.draft_status === "approved"
                    ? "ĐÃ PHÊ DUYỆT"
                    : p.draft_status === "sent"
                    ? "ĐÃ GỬI"
                    : p.draft_status === "failed"
                    ? "TỪ CHỐI / THẤT BẠI"
                    : "CHỜ DUYỆT"}
                </span>
              </div>

              {/* Editable or Static DM Text */}
              {editingDraftId === p.draft_id ? (
                <div className="mb-3 space-y-2">
                  <label className="block text-xs font-semibold text-gray-700">Chỉnh sửa nội dung DM:</label>
                  <textarea
                    className="w-full border border-indigo-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => setEditingDraftId(null)}
                      className="text-xs px-3 py-1.5 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-100"
                    >
                      Hủy
                    </button>
                    <button
                      onClick={() => handleEditSave(p.draft_id)}
                      disabled={loading}
                      className="text-xs px-3.5 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
                    >
                      Lưu nội dung
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mb-3 p-3.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 leading-relaxed font-sans">
                  "{p.draft_text || "(Chưa có văn bản)"}"
                </div>
              )}

              {/* Evidence used */}
              <div className="mb-4 text-xs text-gray-500 bg-white border border-dashed border-gray-200 rounded p-2.5">
                <span className="font-semibold text-gray-600">Bằng chứng thực sử dụng: </span>
                {p.evidence_used || p.bio || "Không có bằng chứng công khai"}
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                {p.draft_status !== "approved" && (
                  <button
                    onClick={() => handleApprove(p.draft_id)}
                    disabled={loading}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3.5 py-1.5 rounded-lg font-medium transition"
                  >
                    ✓ Phê duyệt
                  </button>
                )}
                {editingDraftId !== p.draft_id && (
                  <button
                    onClick={() => handleEditStart(p)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs px-3 py-1.5 rounded-lg font-medium transition"
                  >
                    ✎ Chỉnh sửa
                  </button>
                )}
                {p.draft_status !== "failed" && (
                  <button
                    onClick={() => handleReject(p.draft_id)}
                    disabled={loading}
                    className="bg-gray-100 hover:bg-red-50 hover:text-red-600 text-gray-600 text-xs px-3 py-1.5 rounded-lg font-medium transition"
                  >
                    ✕ Từ chối
                  </button>
                )}
                <button
                  onClick={() => handleRegenerate(p.id)}
                  disabled={loading}
                  className="ml-auto text-xs text-indigo-600 hover:underline"
                >
                  ↻ Soạn lại bằng Claude AI
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
