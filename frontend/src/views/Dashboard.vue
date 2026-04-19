<template>
  <DefaultLayout>
    <div class="command-hub-page">
      <section class="hub-hero">
        <div>
          <p class="hero-kicker">StoryHub POS</p>
          <h1>Chọn Chế Độ Làm Việc</h1>
          <p class="hero-subtitle">Hôm nay cần làm gì? Chọn nhanh bằng phím tắt hoặc bấm vào chế độ tương ứng.</p>
        </div>
        <div class="shift-pill">
          <span class="material-icons">badge</span>
          Nhân viên
        </div>
      </section>

      <section class="mode-grid" aria-label="Command Hub actions">
        <button
          v-for="mode in modes"
          :key="mode.key"
          type="button"
          class="mode-card"
          :class="mode.theme"
          @click="go(mode.route, mode.query)"
        >
          <span class="mode-hotkey">{{ mode.key }}</span>
          <span class="material-icons mode-icon">{{ mode.icon }}</span>
          <span class="mode-title">{{ mode.title }}</span>
          <span class="mode-subtitle">{{ mode.subtitle }}</span>
        </button>
      </section>

      <section class="scan-cta">
        <span class="material-icons">qr_code_scanner</span>
        <div>
          <p class="scan-title">Hoặc quét mã để bắt đầu tự động</p>
          <p class="scan-desc">Mã hợp đồng sẽ vào màn Trả sách. Mã hàng sẽ điều hướng tới Bán hàng hoặc Kho.</p>
        </div>
      </section>

      <HotkeyBar :items="hubHotkeys" />
    </div>
  </DefaultLayout>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";
import { useRouter } from "vue-router";
import DefaultLayout from "../components/layout/defaultLayout.vue";
import HotkeyBar, { type HotkeyItem } from "../components/layout/HotkeyBar.vue";

type HubMode = {
  key: string;
  title: string;
  subtitle: string;
  icon: string;
  theme: string;
  route: string;
  query?: Record<string, string>;
};

interface HotkeyEventDetail {
  name?: "f1" | "f2" | "f3" | "f4" | "f5";
}

const router = useRouter();

const modes: HubMode[] = [
  {
    key: "F1",
    title: "Bán Sách",
    subtitle: "Thu ngân bán lẻ nhanh",
    icon: "shopping_bag",
    theme: "sale",
    route: "/ban-hang",
    query: { mode: "retail" },
  },
  {
    key: "F2",
    title: "Thuê Sách",
    subtitle: "Vào quầy checkout cho thuê",
    icon: "auto_stories",
    theme: "rental",
    route: "/ban-hang",
    query: { mode: "rental", focus: "customer" },
  },
  {
    key: "F3",
    title: "Trả Sách",
    subtitle: "Kiểm định và kết toán hoàn trả",
    icon: "assignment_return",
    theme: "return",
    route: "/hoan-tra",
  },
  {
    key: "F4",
    title: "Nhập Kho",
    subtitle: "Nhập mới hoặc bổ sung tồn",
    icon: "inventory_2",
    theme: "inventory",
    route: "/kho",
  },
  {
    key: "F5",
    title: "Báo Cáo",
    subtitle: "Theo dõi doanh thu và vận hành",
    icon: "monitoring",
    theme: "report",
    route: "/bao-cao",
  },
];

const hubHotkeys: HotkeyItem[] = [
  { key: "F1", label: "Bán sách" },
  { key: "F2", label: "Thuê sách" },
  { key: "F3", label: "Trả sách" },
  { key: "F4", label: "Nhập kho" },
  { key: "F5", label: "Báo cáo" },
];

const hotkeyRouteMap: Record<string, HubMode> = {
  f1: modes[0],
  f2: modes[1],
  f3: modes[2],
  f4: modes[3],
  f5: modes[4],
};

const go = async (path: string, query?: Record<string, string>) => {
  await router.push({ path, query });
};

const handleGlobalHotkey = (event: Event) => {
  const customEvent = event as CustomEvent<HotkeyEventDetail>;
  const hotkey = customEvent.detail?.name;
  if (!hotkey || !hotkeyRouteMap[hotkey]) {
    return;
  }

  const target = hotkeyRouteMap[hotkey];
  void go(target.route, target.query);
};

onMounted(() => {
  window.addEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});

onBeforeUnmount(() => {
  window.removeEventListener("storyhub:hotkey", handleGlobalHotkey as EventListener);
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Archivo+Black&display=swap");

.command-hub-page {
  min-height: 100vh;
  padding: 30px;
  background:
    radial-gradient(circle at 15% 10%, rgba(252, 211, 77, 0.2), transparent 32%),
    radial-gradient(circle at 82% 80%, rgba(14, 165, 233, 0.18), transparent 30%),
    linear-gradient(160deg, #fffef5 0%, #f5f8ff 48%, #f7fffb 100%);
  font-family: "Plus Jakarta Sans", "Segoe UI", sans-serif;
}

.hub-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 24px;
}

.hero-kicker {
  margin: 0 0 8px;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #525252;
  font-weight: 800;
}

.hub-hero h1 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  color: #0f172a;
  letter-spacing: -0.03em;
  font-family: "Archivo Black", "Plus Jakarta Sans", sans-serif;
}

.hero-subtitle {
  margin: 10px 0 0;
  color: #334155;
  font-weight: 600;
}

.shift-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: white;
  padding: 8px 14px;
  color: #334155;
  font-weight: 700;
}

.mode-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 24px;
}

.mode-card {
  border: none;
  position: relative;
  border-radius: 24px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  min-height: 188px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.mode-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 35px -24px rgba(15, 23, 42, 0.38);
}

.mode-hotkey {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.12);
  font-weight: 800;
  font-size: 0.78rem;
}

.mode-icon {
  font-size: 2rem;
}

.mode-title {
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.mode-subtitle {
  color: rgba(15, 23, 42, 0.72);
  font-weight: 600;
  max-width: 240px;
}

.mode-card.sale {
  background: linear-gradient(145deg, #dbeafe, #eff6ff);
  color: #1e3a8a;
}

.mode-card.rental {
  background: linear-gradient(145deg, #dcfce7, #f0fdf4);
  color: #166534;
}

.mode-card.return {
  background: linear-gradient(145deg, #ffedd5, #fff7ed);
  color: #9a3412;
}

.mode-card.inventory {
  background: linear-gradient(145deg, #ede9fe, #f5f3ff);
  color: #5b21b6;
}

.mode-card.report {
  background: linear-gradient(145deg, #fce7f3, #fdf2f8);
  color: #9d174d;
}

.scan-cta {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.82);
  margin-bottom: 20px;
}

.scan-cta .material-icons {
  font-size: 1.6rem;
  color: #0f766e;
}

.scan-title {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 800;
  color: #0f172a;
}

.scan-desc {
  margin: 3px 0 0;
  font-size: 0.86rem;
  color: #475569;
}

@media (max-width: 1000px) {
  .mode-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .command-hub-page {
    padding: 18px;
  }

  .hub-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .mode-grid {
    grid-template-columns: 1fr;
  }

  .mode-card {
    min-height: 160px;
  }
}
</style>
