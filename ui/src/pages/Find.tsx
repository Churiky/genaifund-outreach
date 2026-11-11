import { useEffect, useState } from "react";
import { api } from "../api";

interface FindProps {
  campaignId: number;
  onNavigateToDrafts?: () => void;
}

export default function Find({ campaignId, onNavigateToDrafts }: FindProps) {
  const [seeds, setSeeds] = useState<string[]>([
    "0xCodila",
    "svpino",
    "hardmaru",
    "karpathy",
  ]);
  const [newSeed, setNewSeed] = useState("");
  const [prospects, setProspects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [draftingId, setDraftingId] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  const refreshProspects = () => {
    api.listProspects(campaignId)
      .then(setProspects)
      .catch(() => setProspects([]));
  };

  useEffect(() => {
    refreshProspects();
  }, [campaignId]);

  const addSeed = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSeed.trim()) return;
    const clean = newSeed.trim().replace(/^@/, "");
    if (!seeds.includes(clean)) {
      setSeeds((prev) => [...prev, clean]);
    }
    setNewSeed("");
  };

  const removeSeed = (idx: number) => {
    setSeeds((prev) => prev.filter((_, i) => i !== idx));
  };

  const saveSeeds = async () => {
    setLoading(true);
    setMsg("");
    try {
      for (const s of seeds) {
        await api.addSeed(campaignId, s);
      }
      setMsg("Đã lưu các tài khoản hạt giống vào chiến dịch.");
    } catch (err: any) {
      setMsg("Lỗi lưu seed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runFind = async () => {
    setLoading(true);
    setMsg("");
    try {
      // Ensure seeds are saved
      for (const s of seeds) {
        await api.addSeed(campaignId, s).catch(() => {});
      }
      const res = await api.findProspects(campaignId);
      refreshProspects();

      if (res.created > 0) {
        setMsg(`Tìm thấy thành công ${res.created} ứng viên AI/robotics mới!`);
      } else {
        const errorDetail = res.errors?.length ? ` (${res.errors.join("; ")})` : "";
        setMsg(
          `Không tìm thấy ứng viên mới từ X API${errorDetail}. ` +
          `Vui lòng kiểm tra quyền token X hoặc thử thêm seeds khác.`
        );
      }
    } catch (err: any) {
      setMsg("Lỗi tìm kiếm: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDraft = async (prospectId: number) => {
    setDraftingId(prospectId);
    try {
      await api.createDraft(prospectId);
      refreshProspects();
      setMsg("Đã soạn nháp DM dựa trên bằng chứng thực cho ứng viên.");
    } catch (err: any) {
      setMsg("Lỗi tạo nháp: " + err.message);
    } finally {
      setDraftingId(null);
    }
  };

  const handleBatchDraft = async () => {
    setLoading(true);
    try {
      const res = await api.batchDraftAll(campaignId);
      refreshProspects();
      setMsg(`Đã tạo xong ${res.created_drafts} nháp DM từ bằng chứng thực. Sẵn sàng phê duyệt!`);
    } catch (err: any) {
      setMsg("Lỗi tạo nháp hàng loạt: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Seed Accounts Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-bold text-lg text-gray-900">1. Tài khoản hạt giống (Seed Accounts)</h3>
          <span className="text-xs text-gray-500">Mục tiêu: AI models, robotics, infra, devtools</span>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Nhập các tài khoản X uy tín trong hệ sinh thái AI & robotics để hệ thống quét mạng lưới followers/following:
        </p>

        <form onSubmit={addSeed} className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400 text-sm">@</span>
            <input
              className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500"
              value={newSeed}
              onChange={(e) => setNewSeed(e.target.value)}
              placeholder="vd: robotics_sea, karpathy, le_robot_ai"
            />
          </div>
          <button className="bg-gray-800 hover:bg-gray-900 text-white text-sm px-4 py-2 rounded-lg transition font-medium">
            Thêm seed
          </button>
        </form>

        <div className="flex gap-2 mb-4 flex-wrap">
          {seeds.map((s, i) => (
            <span
              key={i}
              className="bg-indigo-50 border border-indigo-100 text-indigo-800 px-3 py-1.5 rounded-lg flex items-center gap-2 text-sm font-medium"
            >
              @{s}
              <button
                onClick={() => removeSeed(i)}
                className="text-indigo-400 hover:text-red-600 text-base leading-none"
              >
                ×
              </button>
            </span>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={saveSeeds}
            disabled={loading || seeds.length === 0}
            className="bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
          >
            Lưu danh sách seeds
          </button>
          <button
            onClick={runFind}
            disabled={loading || seeds.length === 0}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-5 py-2 rounded-lg font-medium shadow-sm transition disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? "Đang quét mạng lưới..." : "🔍 Quét tìm ứng viên từ Seeds"}
          </button>
        </div>

        {msg && (
          <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 text-indigo-900 rounded-lg text-sm">
            {msg}
          </div>
        )}
      </div>

      {/* Discovered Prospects Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="font-bold text-lg text-gray-900">
              2. Ứng viên phát hiện ({prospects.length})
            </h3>
            <p className="text-xs text-gray-500">
              Điểm phù hợp dựa trên từ khóa AI/Robotics, vai trò Founder/Researcher, và tín hiệu Đông Nam Á.
            </p>
          </div>
          {prospects.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleBatchDraft}
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-3.5 py-2 rounded-lg font-medium shadow-sm transition flex items-center gap-1.5"
              >
                ✨ Soạn nháp cho tất cả ứng viên
              </button>
              {onNavigateToDrafts && (
                <button
                  onClick={onNavigateToDrafts}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3.5 py-2 rounded-lg font-medium shadow-sm transition"
                >
                  Xem & Phê duyệt nháp →
                </button>
              )}
            </div>
          )}
        </div>

        {prospects.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">
            Chưa có ứng viên trong chiến dịch. Nhấn "Quét tìm ứng viên từ Seeds" ở trên để bắt đầu.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200 text-xs uppercase tracking-wider">
                  <th className="pb-3 pr-4">Hồ sơ</th>
                  <th className="pb-3 pr-4">Tên / @Username</th>
                  <th className="pb-3 pr-4">Bio & Dữ liệu</th>
                  <th className="pb-3 pr-4">Điểm phù hợp</th>
                  <th className="pb-3 pr-4">Bằng chứng & Lý do</th>
                  <th className="pb-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {prospects.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50/80 transition">
                    <td className="py-3 pr-4">
                      <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                        {(p.display_name || p.username || "U")[0].toUpperCase()}
                      </div>
                    </td>
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
                    <td className="py-3 pr-4 max-w-[220px]">
                      <div className="text-xs text-gray-700 line-clamp-2">{p.bio || "—"}</div>
                      <div className="text-[10px] text-gray-400 mt-0.5">Từ seed: @{p.source_seed_username}</div>
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-bold font-mono ${
                          p.fit_score >= 60
                            ? "bg-emerald-100 text-emerald-800"
                            : p.fit_score >= 30
                            ? "bg-amber-100 text-amber-800"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {p.fit_score}/100
                      </span>
                    </td>
                    <td className="py-3 pr-4 max-w-[240px]">
                      <p className="text-xs text-gray-600">{p.fit_reason || "Đang đánh giá"}</p>
                    </td>
                    <td className="py-3 text-right">
                      {p.draft_id ? (
                        <span className="text-xs text-emerald-600 font-medium bg-emerald-50 px-2 py-1 rounded">
                          ✓ Đã có nháp ({p.draft_status})
                        </span>
                      ) : (
                        <button
                          onClick={() => handleCreateDraft(p.id)}
                          disabled={draftingId === p.id}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded-lg transition font-medium disabled:opacity-50"
                        >
                          {draftingId === p.id ? "Đang soạn..." : "Soạn DM"}
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
