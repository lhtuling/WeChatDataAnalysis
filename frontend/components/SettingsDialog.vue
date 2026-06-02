<template>
  <div
    v-if="open"
    class="settings-dialog fixed inset-0 z-[120] flex items-center justify-center bg-black/40 px-4 py-4 backdrop-blur-md sm:py-8"
    @click.self="handleClose"
  >
    <div class="settings-dialog-panel flex h-[80vh] min-h-[380px] w-full max-w-[880px] overflow-hidden rounded-[10px] border border-[#e2e2e2] bg-white shadow-2xl">
      <!-- Sidebar -->
      <aside class="flex w-[160px] shrink-0 flex-col bg-[#fcfcfc] border-r border-[#eeeeee]">
        <div class="mt-4 mb-2 flex items-center px-4 gap-2">
          <div class="flex h-6 w-6 items-center justify-center rounded-[5px] bg-[#e7f5ee] text-[#07b75b]">
            <svg class="h-[15px] w-[15px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span class="text-[14px] font-bold text-[#1f1f1f]">设置</span>
        </div>

        <div class="flex-1 space-y-0.5 px-3 py-2 overflow-y-auto scrollbar-custom">
          <button
            v-for="item in settingNavItems"
            :key="item.key"
            type="button"
            class="group flex w-full flex-col items-start rounded-[6px] px-3 py-1.5 text-left transition select-none"
            :class="activeSection === item.key ? 'bg-white shadow-sm ring-1 ring-[#e5e5e5]' : 'hover:bg-[#f0f0f0]/60'"
            @click="scrollToSection(item.key)"
          >
            <div class="text-[12px] font-medium" :class="activeSection === item.key ? 'text-[#111]' : 'text-[#777] group-hover:text-[#333]'">
              {{ item.label }}
            </div>
          </button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="relative flex min-w-0 flex-1 flex-col bg-white">
        <button
          type="button"
          class="absolute right-3 top-3 z-10 flex h-6 w-6 items-center justify-center rounded-md text-[#888] transition hover:bg-[#f2f2f2] hover:text-[#222]"
          title="关闭设置"
          @click="handleClose"
        >
          <svg class="h-[14px] w-[14px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>

        <header class="flex h-12 shrink-0 items-center px-6">
          <div class="flex items-center gap-1.5 text-[#111]">
            <svg class="h-[15px] w-[15px] text-[#666]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h2 class="text-[13px] font-bold">{{ settingNavItems.find(i => i.key === activeSection)?.label || '设置' }}</h2>
          </div>
        </header>

        <div ref="contentScrollRef" class="scrollbar-custom flex-1 overflow-y-auto px-6 pb-8 pt-1 space-y-8" @scroll="onContentScroll">
          
          <div v-if="!isDesktopEnv" class="rounded-[6px] border border-amber-200 bg-amber-50 px-3 py-1.5 text-[11px] leading-relaxed text-amber-900">
            当前为浏览器环境：开机自启动/关闭窗口/更新 不可用；“启动偏好”可正常使用；“后端端口”会尝试同步重启本机后端到新端口。
          </div>

          <section ref="desktopSectionRef">
            <div class="mb-2.5 text-[12px] font-bold text-[#999] tracking-widest">桌面行为</div>
            <div class="overflow-hidden rounded-[10px] border border-[#e7e7e7] bg-white divide-y divide-[#ececec]">
              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">开机自启动</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">系统登录后自动启动桌面端应用</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="desktopAutoLaunch"
                    class="settings-switch shrink-0"
                    :class="switchTrackClass(desktopAutoLaunch, !isDesktopEnv || desktopAutoLaunchLoading)"
                    :disabled="!isDesktopEnv || desktopAutoLaunchLoading"
                    @click="toggleDesktopAutoLaunch"
                  >
                    <span class="settings-switch-thumb" :class="desktopAutoLaunch ? 'translate-x-[20px]' : 'translate-x-0'" />
                  </button>
                </div>
                <div v-if="desktopAutoLaunchError" class="mt-1.5 text-[11px] text-red-600 whitespace-pre-wrap">
                  {{ desktopAutoLaunchError }}
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">关闭窗口行为</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">点击关闭按钮时：默认最小化到托盘</div>
                  </div>
                  <select
                    class="shrink-0 rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#333] outline-none transition focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                    :disabled="!isDesktopEnv || desktopCloseBehaviorLoading"
                    :value="desktopCloseBehavior"
                    @change="onDesktopCloseBehaviorChange"
                  >
                    <option value="tray">最小化到托盘</option>
                    <option value="exit">直接退出</option>
                  </select>
                </div>
                <div v-if="desktopCloseBehaviorError" class="mt-1.5 text-[11px] text-red-600 whitespace-pre-wrap">
                  {{ desktopCloseBehaviorError }}
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">后端端口</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">桌面端：重启内置后端并刷新；网页端：尝试切换端口</div>
                  </div>
                  <div class="flex shrink-0 items-center gap-1.5">
                    <input
                      v-model="desktopBackendPortInput"
                      type="number"
                      min="1"
                      max="65535"
                      class="w-16 rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-center text-[12px] tabular-nums text-[#333] outline-none transition focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                      :disabled="desktopBackendPortLoading || desktopBackendPortApplying"
                      @keyup.enter="onDesktopBackendPortApply"
                    />
                    <button
                      type="button"
                      class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                      :disabled="desktopBackendPortLoading || desktopBackendPortApplying"
                      @click="onDesktopBackendPortApply"
                    >
                      {{ desktopBackendPortApplying ? '...' : '应用' }}
                    </button>
                    <button
                      type="button"
                      class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                      :disabled="desktopBackendPortLoading || desktopBackendPortApplying"
                      @click="onDesktopBackendPortReset"
                    >
                      恢复默认
                    </button>
                  </div>
                </div>
                <div v-if="desktopBackendPortError" class="mt-1.5 text-[11px] text-red-600 whitespace-pre-wrap">
                  {{ desktopBackendPortError }}
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="flex flex-col gap-2.5">
                  <div class="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
                    <div class="min-w-0 flex-1">
                      <div class="text-[13px] font-medium text-[#222]">output 目录</div>
                      <div class="mt-0.5 text-[11px] text-[#909090] break-words">
                        当前：{{ desktopOutputDirText }}
                        <span class="ml-1 text-[#666]">{{ desktopOutputDirIsDefault ? '（默认位置）' : '（自定义位置）' }}</span>
                      </div>
                      <div class="mt-0.5 text-[11px] text-[#909090] break-words">默认：{{ desktopOutputDirDefaultText }}</div>
                      <div v-if="desktopOutputDirPendingText" class="mt-0.5 text-[11px] text-amber-700 break-words">
                        待应用：{{ desktopOutputDirPendingText }}
                      </div>
                      <div v-if="desktopOutputDirUnavailableReason" class="mt-1 text-[11px] text-amber-700 break-words">
                        {{ desktopOutputDirUnavailableReason }}
                      </div>
                    </div>
                    <button
                      type="button"
                      class="shrink-0 rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                      :disabled="!isDesktopEnv || desktopOutputDirLoading || desktopOutputDirApplying"
                      @click="onDesktopOpenOutputDir"
                    >
                      打开当前 output
                    </button>
                  </div>
                  <div class="flex flex-col gap-1.5 sm:flex-row sm:items-center">
                    <input
                      v-model="desktopOutputDirInput"
                      type="text"
                      spellcheck="false"
                      class="min-w-0 flex-1 rounded-[6px] border border-[#e2e2e2] bg-white px-2.5 py-1.5 text-[12px] text-[#333] outline-none transition focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                      :disabled="desktopOutputDirControlsDisabled"
                      :placeholder="desktopOutputDirCanChange ? '选择新的 output 目录' : '当前环境不支持修改 output 目录'"
                      @keyup.enter="onDesktopOutputDirApply"
                    />
                    <div class="flex shrink-0 items-center gap-1.5">
                      <button
                        type="button"
                        class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                        :disabled="desktopOutputDirControlsDisabled"
                        @click="onDesktopChooseOutputDir"
                      >
                        选择文件夹
                      </button>
                      <button
                        type="button"
                        class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                        :disabled="desktopOutputDirControlsDisabled"
                        @click="onDesktopOutputDirApply"
                      >
                        {{ desktopOutputDirApplying ? '迁移中...' : '应用' }}
                      </button>
                      <button
                        type="button"
                        class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                        :disabled="desktopOutputDirControlsDisabled"
                        @click="onDesktopOutputDirReset"
                      >
                        恢复默认
                      </button>
                    </div>
                  </div>
                  <div v-if="desktopOutputDirCanChange" class="text-[11px] text-[#909090]">
                    修改后会迁移整个 output 目录；如果目标目录已有内容，会先阻止并提示。
                  </div>
                  <div v-if="desktopOutputDirProgress" class="rounded-[6px] border border-[#d8efe2] bg-[#f4fbf7] px-2.5 py-2">
                    <div class="flex items-center justify-between gap-3 text-[11px] text-[#1b6b43]">
                      <div class="min-w-0 truncate">{{ desktopOutputDirProgressText }}</div>
                      <div class="shrink-0 tabular-nums">{{ desktopOutputDirProgressPercentText }}</div>
                    </div>
                    <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-[#dceee3]">
                      <div
                        class="h-full rounded-full bg-[#07b75b] transition-[width] duration-200 ease-out"
                        :class="desktopOutputDirProgressIndeterminate ? 'animate-pulse' : ''"
                        :style="{ width: desktopOutputDirProgressBarWidth }"
                      />
                    </div>
                    <div v-if="desktopOutputDirProgressDetail" class="mt-1 text-[10px] text-[#5d7a68] break-all">
                      {{ desktopOutputDirProgressDetail }}
                    </div>
                  </div>
                  <div v-if="desktopOutputDirMessage" class="rounded-[6px] border border-[#d8efe2] bg-[#f4fbf7] px-2.5 py-1.5 text-[11px] text-[#1b6b43] whitespace-pre-wrap">
                    {{ desktopOutputDirMessage }}
                  </div>
                </div>
                <div v-if="desktopOutputDirError" class="mt-1.5 text-[11px] text-red-600 whitespace-pre-wrap">
                  {{ desktopOutputDirError }}
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">日志文件</div>
                    <div class="mt-0.5 text-[11px] text-[#909090] break-words">{{ desktopLogFileText }}</div>
                  </div>
                  <button
                    type="button"
                    class="shrink-0 rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[12px] text-[#222] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="desktopLogFileLoading || desktopLogFileOpening"
                    @click="onOpenBackendLogFile"
                  >
                    {{ desktopLogFileOpening ? '打开中...' : '打开日志' }}
                  </button>
                </div>
                <div v-if="desktopLogFileError" class="mt-1.5 text-[11px] text-red-600 whitespace-pre-wrap">
                  {{ desktopLogFileError }}
                </div>
              </div>
            </div>
          </section>

          <section ref="startupSectionRef">
            <div class="mb-2.5 text-[12px] font-bold text-[#999] tracking-widest">启动偏好</div>
            <div class="overflow-hidden rounded-[10px] border border-[#e7e7e7] bg-white divide-y divide-[#ececec]">
              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">启动后自动开启实时获取</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">进入聊天页后自动打开“实时开关”</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="desktopAutoRealtime"
                    class="settings-switch shrink-0"
                    :class="switchTrackClass(desktopAutoRealtime)"
                    @click="toggleDesktopAutoRealtime"
                  >
                    <span class="settings-switch-thumb" :class="desktopAutoRealtime ? 'translate-x-[20px]' : 'translate-x-0'" />
                  </button>
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">有数据时默认进入聊天页</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">有已解密账号时，打开应用跳转到 /chat</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="desktopDefaultToChatWhenData"
                    class="settings-switch shrink-0"
                    :class="switchTrackClass(desktopDefaultToChatWhenData)"
                    @click="toggleDesktopDefaultToChat"
                  >
                    <span class="settings-switch-thumb" :class="desktopDefaultToChatWhenData ? 'translate-x-[20px]' : 'translate-x-0'" />
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section ref="keywordMonitorSectionRef">
            <div class="mb-2.5 flex items-center justify-between gap-3">
              <div class="text-[12px] font-bold text-[#999] tracking-widest">关键词监控</div>
              <div class="text-[11px] text-[#999] tabular-nums">{{ keywordMonitorSummaryText }}</div>
            </div>
            <div class="overflow-hidden rounded-[10px] border border-[#e7e7e7] bg-white divide-y divide-[#ececec]">
              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">启用监控</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">首次启用会从当前消息位置开始记录</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="keywordMonitorEnabled"
                    class="settings-switch shrink-0"
                    :class="switchTrackClass(keywordMonitorEnabled, keywordMonitorLoading || !selectedAccount)"
                    :disabled="keywordMonitorLoading || !selectedAccount"
                    @click="keywordMonitorEnabled = !keywordMonitorEnabled"
                  >
                    <span class="settings-switch-thumb" :class="keywordMonitorEnabled ? 'translate-x-[20px]' : 'translate-x-0'" />
                  </button>
                </div>
              </div>

              <div class="grid gap-3 px-3.5 py-3 sm:grid-cols-2">
                <label class="min-w-0">
                  <div class="mb-1.5 text-[12px] font-medium text-[#333]">监控关键词</div>
                  <textarea
                    v-model="keywordMonitorKeywordsText"
                    rows="5"
                    spellcheck="false"
                    class="h-[108px] w-full resize-none rounded-[6px] border border-[#e2e2e2] bg-white px-2.5 py-2 text-[12px] leading-relaxed text-[#333] outline-none transition placeholder:text-[#aaa] focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                    placeholder="一行一个关键词"
                  />
                </label>
                <label class="min-w-0">
                  <div class="mb-1.5 text-[12px] font-medium text-[#333]">过滤关键词</div>
                  <textarea
                    v-model="keywordMonitorFilterText"
                    rows="5"
                    spellcheck="false"
                    class="h-[108px] w-full resize-none rounded-[6px] border border-[#e2e2e2] bg-white px-2.5 py-2 text-[12px] leading-relaxed text-[#333] outline-none transition placeholder:text-[#aaa] focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                    placeholder="命中后排除"
                  />
                </label>
                <div class="sm:col-span-2 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    class="rounded-[6px] border border-[#d8efe2] bg-[#f4fbf7] px-3 py-1.5 text-[12px] font-medium text-[#147345] transition hover:bg-[#eaf8f0] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="keywordMonitorSaving || keywordMonitorLoading || !selectedAccount"
                    @click="saveKeywordMonitor"
                  >
                    {{ keywordMonitorSaving ? '保存中...' : '保存设置' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-[6px] border border-[#e2e2e2] bg-white px-3 py-1.5 text-[12px] text-[#333] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="keywordMonitorProcessing || !selectedAccount"
                    @click="processKeywordMonitorNow"
                  >
                    {{ keywordMonitorProcessing ? '处理中...' : '立即处理' }}
                  </button>
                  <button
                    type="button"
                    class="rounded-[6px] border border-[#e2e2e2] bg-white px-3 py-1.5 text-[12px] text-[#333] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="keywordMonitorReadAllLoading || keywordMonitorUnread <= 0"
                    @click="markAllKeywordMonitorHitsRead"
                  >
                    全部已读
                  </button>
                  <span v-if="keywordMonitorMessage" class="text-[11px] text-[#1b6b43]">{{ keywordMonitorMessage }}</span>
                  <span v-if="keywordMonitorError" class="text-[11px] text-red-600">{{ keywordMonitorError }}</span>
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <div class="text-[12px] font-medium text-[#333]">过滤群</div>
                  <div class="text-[11px] text-[#999]">{{ keywordMonitorExcludedGroups.length }} / {{ keywordMonitorGroups.length }}</div>
                </div>
                <input
                  v-model="keywordMonitorGroupQuery"
                  type="text"
                  spellcheck="false"
                  class="mb-2 w-full rounded-[6px] border border-[#e2e2e2] bg-white px-2.5 py-1.5 text-[12px] text-[#333] outline-none transition placeholder:text-[#aaa] focus:border-[#07b75b] focus:ring-1 focus:ring-[#07b75b]/30"
                  placeholder="搜索群名"
                />
                <div class="max-h-[156px] overflow-y-auto rounded-[6px] border border-[#ededed] bg-[#fcfcfc]">
                  <label
                    v-for="group in filteredKeywordMonitorGroups"
                    :key="group.username"
                    class="flex cursor-pointer items-center gap-2 border-b border-[#f0f0f0] px-2.5 py-2 last:border-b-0 hover:bg-white"
                    :class="{ 'privacy-blur': privacyMode }"
                  >
                    <input
                      type="checkbox"
                      class="h-3.5 w-3.5 accent-[#07b75b]"
                      :checked="isKeywordMonitorGroupExcluded(group.username)"
                      @change="toggleKeywordMonitorGroup(group)"
                    />
                    <span class="min-w-0 flex-1 truncate text-[12px] text-[#333]">{{ group.name || group.username }}</span>
                    <span v-if="isKeywordMonitorGroupExcluded(group.username)" class="shrink-0 text-[10px] text-[#999]">已过滤</span>
                  </label>
                  <div v-if="!keywordMonitorGroupsLoading && filteredKeywordMonitorGroups.length === 0" class="px-2.5 py-3 text-center text-[11px] text-[#999]">
                    暂无群聊
                  </div>
                  <div v-if="keywordMonitorGroupsLoading" class="px-2.5 py-3 text-center text-[11px] text-[#999]">
                    加载中...
                  </div>
                </div>
              </div>

              <div class="px-3.5 py-3">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <div class="text-[12px] font-medium text-[#333]">命中记录</div>
                  <button
                    type="button"
                    class="rounded-[6px] border border-[#e2e2e2] bg-white px-2 py-1 text-[11px] text-[#333] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="keywordMonitorHitsLoading || !selectedAccount"
                    @click="refreshKeywordMonitorHits"
                  >
                    刷新
                  </button>
                </div>
                <div class="max-h-[260px] overflow-y-auto rounded-[6px] border border-[#ededed] bg-[#fcfcfc]">
                  <button
                    v-for="hit in keywordMonitorHits"
                    :key="hit.id"
                    type="button"
                    class="block w-full border-b border-[#f0f0f0] px-3 py-2.5 text-left transition last:border-b-0 hover:bg-white"
                    @click="openKeywordMonitorHit(hit)"
                  >
                    <div class="mb-1 flex min-w-0 items-center gap-2 text-[11px] text-[#777]">
                      <span v-if="!hit.isRead" class="h-1.5 w-1.5 shrink-0 rounded-full bg-[#ff4d4f]" />
                      <span class="truncate font-medium text-[#333]" :class="{ 'privacy-blur': privacyMode }">{{ hit.conversationName || hit.username }}</span>
                      <span class="shrink-0">·</span>
                      <span class="truncate" :class="{ 'privacy-blur': privacyMode }">{{ hit.senderDisplayName || hit.senderUsername || '未知' }}</span>
                      <span class="shrink-0 tabular-nums">{{ formatKeywordMonitorTime(hit.createTime) }}</span>
                    </div>
                    <div class="max-h-[72px] overflow-hidden whitespace-pre-wrap break-words text-[12px] leading-relaxed text-[#222]" :class="{ 'privacy-blur': privacyMode }">
                      {{ hit.content }}
                    </div>
                    <div class="mt-1 flex flex-wrap gap-1">
                      <span
                        v-for="kw in hit.matchedKeywords"
                        :key="`${hit.id}-${kw}`"
                        class="rounded-[4px] bg-[#eaf8f0] px-1.5 py-0.5 text-[10px] text-[#147345]"
                      >
                        {{ kw }}
                      </span>
                    </div>
                  </button>
                  <div v-if="!keywordMonitorHitsLoading && keywordMonitorHits.length === 0" class="px-2.5 py-4 text-center text-[11px] text-[#999]">
                    暂无记录
                  </div>
                  <div v-if="keywordMonitorHitsLoading" class="px-2.5 py-4 text-center text-[11px] text-[#999]">
                    加载中...
                  </div>
                </div>
                <div v-if="keywordMonitorHasMore" class="mt-2 flex justify-center">
                  <button
                    type="button"
                    class="rounded-[6px] border border-[#e2e2e2] bg-white px-3 py-1.5 text-[12px] text-[#333] transition hover:bg-[#f9f9f9] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="keywordMonitorHitsLoading"
                    @click="loadMoreKeywordMonitorHits"
                  >
                    加载更多
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section ref="updatesSectionRef">
            <div class="mb-2.5 text-[12px] font-bold text-[#999] tracking-widest">更新</div>
            <div class="overflow-hidden rounded-[10px] border border-[#e7e7e7] bg-white divide-y divide-[#ececec]">
              <div class="px-3.5 py-3">
                <div class="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">当前版本</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">{{ desktopVersionText }}</div>
                  </div>
                  <button
                    type="button"
                    class="shrink-0 rounded-[6px] border border-[#e2e2e2] bg-[#fafafa] px-2.5 py-1 text-[12px] text-[#222] transition hover:bg-[#f0f0f0] disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="!isDesktopEnv || desktopUpdate.manualCheckLoading.value"
                    @click="onDesktopCheckUpdates"
                  >
                    {{ desktopUpdate.manualCheckLoading.value ? '检查中...' : '检查桌面版更新' }}
                  </button>
                </div>
                <div v-if="desktopUpdate.lastCheckMessage.value" class="mt-2 rounded-[6px] bg-[#f9f9f9] border border-[#eee] px-2.5 py-1.5 text-[11px] text-[#666] whitespace-pre-wrap break-words">
                  {{ desktopUpdate.lastCheckMessage.value }}
                </div>
              </div>
            </div>
          </section>

          <section ref="snsSectionRef">
            <div class="mb-2.5 text-[12px] font-bold text-[#999] tracking-widest">朋友圈</div>
            <div class="overflow-hidden rounded-[10px] border border-[#e7e7e7] bg-white divide-y divide-[#ececec]">
              <div class="px-3.5 py-3">
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="text-[13px] font-medium text-[#222]">朋友圈图片使用缓存</div>
                    <div class="mt-0.5 text-[11px] text-[#909090]">开启：下载解密失败时回退本地缓存（默认）；关闭：始终重新下载</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="snsUseCache"
                    class="settings-switch shrink-0"
                    :class="switchTrackClass(snsUseCache)"
                    @click="toggleSnsUseCache"
                  >
                    <span class="settings-switch-thumb" :class="snsUseCache ? 'translate-x-[20px]' : 'translate-x-0'" />
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { useChatAccountsStore } from '~/stores/chatAccounts'
import { usePrivacyStore } from '~/stores/privacy'
import { DESKTOP_SETTING_AUTO_REALTIME_KEY, DESKTOP_SETTING_DEFAULT_TO_CHAT_KEY, SNS_SETTING_USE_CACHE_KEY, readLocalBoolSetting, writeLocalBoolSetting } from '~/lib/desktop-settings'
import { readApiBaseOverride, writeApiBaseOverride } from '~/lib/api-settings'
import { invalidateApiBaseCache } from '~/composables/useApiBase'
import { reportServerErrorFromError } from '~/lib/server-error-logging'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const settingNavItems = [
  { key: 'desktop', label: '桌面行为', hint: '启动 / 关闭 / 端口' },
  { key: 'startup', label: '启动偏好', hint: '自动实时 / 默认页面' },
  { key: 'keywordMonitor', label: '关键词监控', hint: '规则 / 记录' },
  { key: 'updates', label: '更新', hint: '版本信息 / 检查更新' },
  { key: 'sns', label: '朋友圈', hint: '图片缓存策略' },
]

const api = useApi()
const { targetSection } = useSettingsDialog()
const chatAccounts = useChatAccountsStore()
const { selectedAccount } = storeToRefs(chatAccounts)
const privacyStore = usePrivacyStore()
const { privacyMode } = storeToRefs(privacyStore)

const activeSection = ref(settingNavItems[0].key)
const contentScrollRef = ref(null)
const desktopSectionRef = ref(null)
const startupSectionRef = ref(null)
const keywordMonitorSectionRef = ref(null)
const updatesSectionRef = ref(null)
const snsSectionRef = ref(null)

const isDesktopEnv = ref(false)
const desktopUpdate = useDesktopUpdate()

const desktopVersionText = computed(() => {
  if (!isDesktopEnv.value) return '仅桌面端可用'
  const v = String(desktopUpdate.currentVersion.value || '').trim()
  return v || '—'
})

const desktopAutoRealtime = ref(false)
const desktopDefaultToChatWhenData = ref(false)
const snsUseCache = ref(true)

const desktopAutoLaunch = ref(false)
const desktopAutoLaunchLoading = ref(false)
const desktopAutoLaunchError = ref('')

const desktopCloseBehavior = ref('tray')
const desktopCloseBehaviorLoading = ref(false)
const desktopCloseBehaviorError = ref('')

const desktopBackendPortInput = ref('')
const desktopBackendPortLoading = ref(false)
const desktopBackendPortApplying = ref(false)
const desktopBackendPortError = ref('')
const desktopBackendPortDefault = ref(10392)

const desktopOutputDir = ref('')
const desktopOutputDirDefault = ref('')
const desktopOutputDirInput = ref('')
const desktopOutputDirPending = ref('')
const desktopOutputDirLoading = ref(false)
const desktopOutputDirApplying = ref(false)
const desktopOutputDirError = ref('')
const desktopOutputDirMessage = ref('')
const desktopOutputDirIsDefault = ref(true)
const desktopOutputDirCanChange = ref(true)
const desktopOutputDirUnavailableReason = ref('')
const desktopOutputDirProgress = ref(null)
let removeDesktopOutputDirProgressListener = null
const desktopOutputDirText = computed(() => {
  if (!isDesktopEnv.value) return '仅桌面端可用'
  const v = String(desktopOutputDir.value || '').trim()
  return v || '—'
})
const desktopOutputDirDefaultText = computed(() => {
  if (!isDesktopEnv.value) return '仅桌面端可用'
  const v = String(desktopOutputDirDefault.value || '').trim()
  return v || '—'
})
const desktopOutputDirPendingText = computed(() => {
  const v = String(desktopOutputDirPending.value || '').trim()
  return v || ''
})
const desktopOutputDirProgressPercent = computed(() => {
  const n = Number(desktopOutputDirProgress.value?.percent || 0)
  if (!Number.isFinite(n) || n < 0) return 0
  return Math.max(0, Math.min(100, Math.round(n)))
})
const desktopOutputDirProgressPercentText = computed(() => `${desktopOutputDirProgressPercent.value}%`)
const desktopOutputDirProgressText = computed(() => {
  const text = String(desktopOutputDirProgress.value?.message || '').trim()
  return text || '正在迁移 output 目录'
})
const desktopOutputDirProgressIndeterminate = computed(() => {
  const stage = String(desktopOutputDirProgress.value?.stage || '').trim()
  return stage === 'preparing' || stage === 'scanning' || stage === 'rolling-back' || stage === 'restarting'
})
const desktopOutputDirProgressBarWidth = computed(() => {
  if (!desktopOutputDirProgress.value) return '0%'
  if (desktopOutputDirProgressIndeterminate.value) return '28%'
  return `${Math.max(6, desktopOutputDirProgressPercent.value)}%`
})
const desktopOutputDirProgressDetail = computed(() => {
  const progress = desktopOutputDirProgress.value
  if (!progress) return ''

  const parts = []
  const bytesTotal = Number(progress.bytesTotal || 0)
  const bytesTransferred = Number(progress.bytesTransferred || 0)
  const itemsTotal = Number(progress.itemsTotal || 0)
  const itemsTransferred = Number(progress.itemsTransferred || 0)

  if (bytesTotal > 0) {
    parts.push(`${formatBytes(bytesTransferred)} / ${formatBytes(bytesTotal)}`)
  } else if (itemsTotal > 0) {
    parts.push(`${Math.min(itemsTransferred, itemsTotal)} / ${itemsTotal} 项`)
  }

  const currentFile = String(progress.currentFile || '').trim()
  if (currentFile) {
    parts.push(currentFile)
  }

  return parts.join(' · ')
})
const desktopOutputDirControlsDisabled = computed(() => (
  !isDesktopEnv.value || !desktopOutputDirCanChange.value || desktopOutputDirLoading.value || desktopOutputDirApplying.value
))

const desktopLogFilePath = ref('')
const desktopLogFileLoading = ref(false)
const desktopLogFileOpening = ref(false)
const desktopLogFileError = ref('')
const desktopLogFileText = computed(() => {
  const v = String(desktopLogFilePath.value || '').trim()
  return v || '—'
})

const keywordMonitorEnabled = ref(false)
const keywordMonitorKeywordsText = ref('')
const keywordMonitorFilterText = ref('')
const keywordMonitorExcludedGroups = ref([])
const keywordMonitorGroups = ref([])
const keywordMonitorHits = ref([])
const keywordMonitorGroupQuery = ref('')
const keywordMonitorLoading = ref(false)
const keywordMonitorSaving = ref(false)
const keywordMonitorProcessing = ref(false)
const keywordMonitorGroupsLoading = ref(false)
const keywordMonitorHitsLoading = ref(false)
const keywordMonitorReadAllLoading = ref(false)
const keywordMonitorError = ref('')
const keywordMonitorMessage = ref('')
const keywordMonitorTotal = ref(0)
const keywordMonitorUnread = ref(0)
const keywordMonitorHasMore = ref(false)
const keywordMonitorLimit = 50
const keywordMonitorOffset = ref(0)

const keywordMonitorSummaryText = computed(() => {
  const unread = Number(keywordMonitorUnread.value || 0)
  const total = Number(keywordMonitorTotal.value || 0)
  if (!selectedAccount.value) return '未选择账号'
  if (!keywordMonitorEnabled.value && total <= 0) return '未启用'
  return unread > 0 ? `${unread} 未读 / ${total} 条` : `${total} 条`
})

const filteredKeywordMonitorGroups = computed(() => {
  const q = String(keywordMonitorGroupQuery.value || '').trim().toLowerCase()
  const groups = Array.isArray(keywordMonitorGroups.value) ? keywordMonitorGroups.value : []
  if (!q) return groups
  return groups.filter((group) => {
    const name = String(group?.name || '').toLowerCase()
    const username = String(group?.username || '').toLowerCase()
    return name.includes(q) || username.includes(q)
  })
})

const switchTrackClass = (enabled, disabled = false) => {
  if (disabled) return enabled ? 'bg-[#07b75b] opacity-50 cursor-not-allowed' : 'bg-[#d0d0d0] opacity-50 cursor-not-allowed'
  return enabled ? 'bg-[#07b75b] hover:brightness-95' : 'bg-[#d0d0d0] hover:brightness-95'
}

const formatBytes = (value) => {
  const n = Number(value || 0)
  if (!Number.isFinite(n) || n <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let next = n
  let unitIndex = 0
  while (next >= 1024 && unitIndex < units.length - 1) {
    next /= 1024
    unitIndex += 1
  }
  const digits = next >= 100 || unitIndex === 0 ? 0 : next >= 10 ? 1 : 2
  return `${next.toFixed(digits)} ${units[unitIndex]}`
}

const applyDesktopOutputDirProgress = (progress) => {
  if (!progress || progress.active === false) {
    desktopOutputDirProgress.value = null
    return
  }
  desktopOutputDirProgress.value = { ...progress }
}

const refreshDesktopOutputDirProgress = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.getOutputDirChangeProgress) return
  try {
    const progress = await window.wechatDesktop.getOutputDirChangeProgress()
    applyDesktopOutputDirProgress(progress)
  } catch {}
}

const sectionElements = computed(() => [
  { key: 'desktop', el: desktopSectionRef.value },
  { key: 'startup', el: startupSectionRef.value },
  { key: 'keywordMonitor', el: keywordMonitorSectionRef.value },
  { key: 'updates', el: updatesSectionRef.value },
  { key: 'sns', el: snsSectionRef.value },
])

const scrollToSection = (key) => {
  const scrollHost = contentScrollRef.value
  const target = sectionElements.value.find((item) => item.key === key)?.el
  activeSection.value = key
  if (!scrollHost || !target) return
  scrollHost.scrollTo({
    top: Math.max(0, target.offsetTop - 10),
    behavior: 'smooth',
  })
}

const onContentScroll = () => {
  const scrollHost = contentScrollRef.value
  if (!scrollHost) return
  const position = scrollHost.scrollTop + 120
  let current = settingNavItems[0].key
  for (const section of sectionElements.value) {
    if (!section.el) continue
    if (section.el.offsetTop <= position) current = section.key
  }
  activeSection.value = current
}

const handleClose = () => {
  emit('close')
}

const onEscKeydown = (event) => {
  if (event?.key !== 'Escape') return
  event.preventDefault()
  handleClose()
}

const fetchAdminEndpoint = async (url, options = {}) => {
  const apiBase = useApiBase()
  try {
    return await $fetch(url, {
      baseURL: apiBase,
      ...options,
    })
  } catch (e) {
    await reportServerErrorFromError(e, {
      method: options?.method || 'GET',
      requestUrl: url,
      source: 'SettingsDialog',
      apiBase,
    })
    throw e
  }
}

const splitKeywordMonitorText = (value) => {
  const seen = new Set()
  return String(value || '')
    .split(/[\n\r,，;；]+/)
    .map((item) => String(item || '').trim())
    .filter((item) => {
      if (!item) return false
      const key = item.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
}

const formatKeywordMonitorText = (value) => {
  if (!Array.isArray(value)) return ''
  return value.map((item) => String(item || '').trim()).filter(Boolean).join('\n')
}

const normalizeKeywordMonitorGroup = (group) => ({
  username: String(group?.username || '').trim(),
  name: String(group?.name || '').trim(),
})

const applyKeywordMonitorSettings = (settings) => {
  keywordMonitorEnabled.value = !!settings?.enabled
  keywordMonitorKeywordsText.value = formatKeywordMonitorText(settings?.monitorKeywords || [])
  keywordMonitorFilterText.value = formatKeywordMonitorText(settings?.filterKeywords || [])
  keywordMonitorExcludedGroups.value = Array.isArray(settings?.excludedGroups)
    ? settings.excludedGroups.map(normalizeKeywordMonitorGroup).filter((group) => group.username)
    : []
}

const resetKeywordMonitorState = () => {
  keywordMonitorEnabled.value = false
  keywordMonitorKeywordsText.value = ''
  keywordMonitorFilterText.value = ''
  keywordMonitorExcludedGroups.value = []
  keywordMonitorGroups.value = []
  keywordMonitorHits.value = []
  keywordMonitorGroupQuery.value = ''
  keywordMonitorTotal.value = 0
  keywordMonitorUnread.value = 0
  keywordMonitorHasMore.value = false
  keywordMonitorOffset.value = 0
  keywordMonitorError.value = ''
  keywordMonitorMessage.value = ''
}

const refreshKeywordMonitorSettings = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account) {
    resetKeywordMonitorState()
    return
  }
  const res = await api.getKeywordMonitorSettings({ account })
  applyKeywordMonitorSettings(res || {})
}

const refreshKeywordMonitorGroups = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account) {
    keywordMonitorGroups.value = []
    return
  }
  keywordMonitorGroupsLoading.value = true
  try {
    const res = await api.listKeywordMonitorGroups({ account })
    keywordMonitorGroups.value = Array.isArray(res?.groups) ? res.groups.map(normalizeKeywordMonitorGroup).filter((group) => group.username) : []
  } finally {
    keywordMonitorGroupsLoading.value = false
  }
}

const refreshKeywordMonitorSummary = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account) {
    keywordMonitorTotal.value = 0
    keywordMonitorUnread.value = 0
    return
  }
  const res = await api.getKeywordMonitorSummary({ account })
  if (res && Object.prototype.hasOwnProperty.call(res, 'enabled')) {
    keywordMonitorEnabled.value = !!res.enabled
  }
  keywordMonitorTotal.value = Number(res?.total || 0)
  keywordMonitorUnread.value = Number(res?.unread || 0)
}

const refreshKeywordMonitorHits = async (options = {}) => {
  const account = String(selectedAccount.value || '').trim()
  const append = !!options.append
  if (!account) {
    keywordMonitorHits.value = []
    keywordMonitorHasMore.value = false
    return
  }
  keywordMonitorHitsLoading.value = true
  try {
    const offset = append ? Number(keywordMonitorOffset.value || 0) : 0
    const res = await api.listKeywordMonitorHits({ account, limit: keywordMonitorLimit, offset })
    const hits = Array.isArray(res?.hits) ? res.hits : []
    keywordMonitorHits.value = append ? [...keywordMonitorHits.value, ...hits] : hits
    keywordMonitorOffset.value = offset + hits.length
    keywordMonitorTotal.value = Number(res?.total || keywordMonitorTotal.value || 0)
    keywordMonitorHasMore.value = !!res?.hasMore
  } finally {
    keywordMonitorHitsLoading.value = false
  }
}

const refreshKeywordMonitorAll = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account) {
    resetKeywordMonitorState()
    return
  }
  keywordMonitorLoading.value = true
  keywordMonitorError.value = ''
  keywordMonitorMessage.value = ''
  try {
    await refreshKeywordMonitorSettings()
    await Promise.all([
      refreshKeywordMonitorGroups(),
      refreshKeywordMonitorHits(),
      refreshKeywordMonitorSummary(),
    ])
  } catch (e) {
    keywordMonitorError.value = e?.message || '读取关键词监控失败'
  } finally {
    keywordMonitorLoading.value = false
  }
}

const isKeywordMonitorGroupExcluded = (username) => {
  const key = String(username || '').trim()
  return !!key && keywordMonitorExcludedGroups.value.some((group) => String(group?.username || '').trim() === key)
}

const toggleKeywordMonitorGroup = (group) => {
  const normalized = normalizeKeywordMonitorGroup(group)
  if (!normalized.username) return
  if (isKeywordMonitorGroupExcluded(normalized.username)) {
    keywordMonitorExcludedGroups.value = keywordMonitorExcludedGroups.value.filter(
      (item) => String(item?.username || '').trim() !== normalized.username
    )
  } else {
    keywordMonitorExcludedGroups.value = [...keywordMonitorExcludedGroups.value, normalized]
  }
}

const saveKeywordMonitor = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account || keywordMonitorSaving.value) return
  const monitorKeywords = splitKeywordMonitorText(keywordMonitorKeywordsText.value)
  if (keywordMonitorEnabled.value && monitorKeywords.length === 0) {
    keywordMonitorError.value = '启用监控前需要填写监控关键词'
    keywordMonitorMessage.value = ''
    return
  }

  keywordMonitorSaving.value = true
  keywordMonitorError.value = ''
  keywordMonitorMessage.value = ''
  try {
    const res = await api.saveKeywordMonitorSettings({
      account,
      enabled: !!keywordMonitorEnabled.value,
      monitorKeywords,
      filterKeywords: splitKeywordMonitorText(keywordMonitorFilterText.value),
      excludedGroups: keywordMonitorExcludedGroups.value.map(normalizeKeywordMonitorGroup).filter((group) => group.username),
    })
    applyKeywordMonitorSettings(res || {})
    keywordMonitorMessage.value = Number(res?.baselineTables || 0) > 0 ? '设置已保存，当前基线已建立' : '设置已保存'
    await Promise.all([
      refreshKeywordMonitorSummary(),
      refreshKeywordMonitorHits(),
    ])
  } catch (e) {
    keywordMonitorError.value = e?.message || '保存关键词监控失败'
  } finally {
    keywordMonitorSaving.value = false
  }
}

const processKeywordMonitorNow = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account || keywordMonitorProcessing.value) return
  keywordMonitorProcessing.value = true
  keywordMonitorError.value = ''
  keywordMonitorMessage.value = ''
  try {
    const res = await api.processKeywordMonitor({ account })
    keywordMonitorMessage.value = res?.status === 'skipped'
      ? '当前无需处理'
      : `已处理，新增 ${Number(res?.inserted || 0)} 条`
    await Promise.all([
      refreshKeywordMonitorSummary(),
      refreshKeywordMonitorHits(),
    ])
  } catch (e) {
    keywordMonitorError.value = e?.message || '处理关键词监控失败'
  } finally {
    keywordMonitorProcessing.value = false
  }
}

const markAllKeywordMonitorHitsRead = async () => {
  const account = String(selectedAccount.value || '').trim()
  if (!account || keywordMonitorReadAllLoading.value || keywordMonitorUnread.value <= 0) return
  keywordMonitorReadAllLoading.value = true
  keywordMonitorError.value = ''
  try {
    await api.markKeywordMonitorHitsRead({ account })
    keywordMonitorHits.value = keywordMonitorHits.value.map((hit) => ({ ...hit, isRead: true }))
    await refreshKeywordMonitorSummary()
  } catch (e) {
    keywordMonitorError.value = e?.message || '标记已读失败'
  } finally {
    keywordMonitorReadAllLoading.value = false
  }
}

const loadMoreKeywordMonitorHits = async () => {
  if (!keywordMonitorHasMore.value || keywordMonitorHitsLoading.value) return
  await refreshKeywordMonitorHits({ append: true })
}

const formatKeywordMonitorTime = (value) => {
  const n = Number(value || 0)
  if (!Number.isFinite(n) || n <= 0) return ''
  const ms = n > 1_000_000_000_000 ? n : n * 1000
  try {
    return new Date(ms).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

const openKeywordMonitorHit = async (hit) => {
  const account = String(selectedAccount.value || '').trim()
  const username = String(hit?.username || '').trim()
  const messageId = String(hit?.messageId || '').trim()
  const hitId = Number(hit?.id || 0)
  if (!account || !username || !messageId) return
  try {
    if (hitId > 0 && !hit?.isRead) {
      await api.markKeywordMonitorHitsRead({ account, hitIds: [hitId] })
      keywordMonitorHits.value = keywordMonitorHits.value.map((item) => (
        Number(item?.id || 0) === hitId ? { ...item, isRead: true } : item
      ))
      await refreshKeywordMonitorSummary()
    }
  } catch {}
  handleClose()
  await navigateTo({
    path: `/chat/${encodeURIComponent(username)}`,
    query: {
      anchor_id: messageId,
      monitor_hit: hitId > 0 ? String(hitId) : undefined,
    },
  })
}

const scrollToTargetSection = async () => {
  const key = String(targetSection.value || '').trim()
  if (!key) return
  await nextTick()
  if (sectionElements.value.some((item) => item.key === key)) {
    scrollToSection(key)
  }
}

const refreshDesktopAutoLaunch = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.getAutoLaunch) return
  desktopAutoLaunchLoading.value = true
  desktopAutoLaunchError.value = ''
  try {
    desktopAutoLaunch.value = !!(await window.wechatDesktop.getAutoLaunch())
  } catch (e) {
    desktopAutoLaunchError.value = e?.message || '读取开机自启动状态失败'
  } finally {
    desktopAutoLaunchLoading.value = false
  }
}

const setDesktopAutoLaunch = async (enabled) => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.setAutoLaunch) return
  desktopAutoLaunchLoading.value = true
  desktopAutoLaunchError.value = ''
  try {
    desktopAutoLaunch.value = !!(await window.wechatDesktop.setAutoLaunch(!!enabled))
  } catch (e) {
    desktopAutoLaunchError.value = e?.message || '设置开机自启动失败'
    await refreshDesktopAutoLaunch()
  } finally {
    desktopAutoLaunchLoading.value = false
  }
}

const refreshDesktopCloseBehavior = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.getCloseBehavior) return
  desktopCloseBehaviorLoading.value = true
  desktopCloseBehaviorError.value = ''
  try {
    const v = await window.wechatDesktop.getCloseBehavior()
    desktopCloseBehavior.value = String(v || '').toLowerCase() === 'exit' ? 'exit' : 'tray'
  } catch (e) {
    desktopCloseBehaviorError.value = e?.message || '读取关闭窗口行为失败'
  } finally {
    desktopCloseBehaviorLoading.value = false
  }
}

const setDesktopCloseBehavior = async (behavior) => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.setCloseBehavior) return
  const desired = String(behavior || '').toLowerCase() === 'exit' ? 'exit' : 'tray'
  desktopCloseBehaviorLoading.value = true
  desktopCloseBehaviorError.value = ''
  try {
    const v = await window.wechatDesktop.setCloseBehavior(desired)
    desktopCloseBehavior.value = String(v || '').toLowerCase() === 'exit' ? 'exit' : 'tray'
  } catch (e) {
    desktopCloseBehaviorError.value = e?.message || '设置关闭窗口行为失败'
    await refreshDesktopCloseBehavior()
  } finally {
    desktopCloseBehaviorLoading.value = false
  }
}

const refreshDesktopBackendPort = async () => {
  if (!process.client || typeof window === 'undefined') return
  desktopBackendPortLoading.value = true
  desktopBackendPortError.value = ''
  try {
    if (window.wechatDesktop?.getBackendPort) {
      const v = await window.wechatDesktop.getBackendPort()
      const n = Number(v)
      if (Number.isInteger(n) && n >= 1 && n <= 65535) {
        desktopBackendPortInput.value = String(n)
        return
      }
    }

    try {
      const resp = await fetchAdminEndpoint('/admin/port')
      const n = Number(resp?.port)
      const d = Number(resp?.default_port)
      if (Number.isInteger(d) && d >= 1 && d <= 65535) desktopBackendPortDefault.value = d
      if (Number.isInteger(n) && n >= 1 && n <= 65535) {
        desktopBackendPortInput.value = String(n)
        return
      }
    } catch {}

    let detectedPort = null
    const override = readApiBaseOverride()
    if (override && /^https?:\/\//i.test(override)) {
      try {
        const u = new URL(override)
        const n = Number(u.port)
        if (Number.isInteger(n) && n >= 1 && n <= 65535) detectedPort = n
      } catch {}
    }
    if (!desktopBackendPortInput.value) desktopBackendPortInput.value = String(detectedPort ?? 10392)
  } catch (e) {
    desktopBackendPortError.value = e?.message || '读取后端端口失败'
  } finally {
    desktopBackendPortLoading.value = false
  }
}

const refreshDesktopOutputDir = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.getOutputDir && !window.wechatDesktop?.getOutputDirInfo) return
  desktopOutputDirLoading.value = true
  desktopOutputDirError.value = ''
  try {
    if (window.wechatDesktop?.getOutputDirInfo) {
      const info = await window.wechatDesktop.getOutputDirInfo()
      desktopOutputDir.value = String(info?.path || '').trim()
      desktopOutputDirDefault.value = String(info?.defaultPath || '').trim()
      desktopOutputDirPending.value = String(info?.pendingPath || '').trim()
      desktopOutputDirIsDefault.value = !!info?.isDefault
      desktopOutputDirCanChange.value = info?.canChange !== false
      desktopOutputDirUnavailableReason.value = String(info?.changeUnavailableReason || '').trim()
      desktopOutputDirInput.value = desktopOutputDir.value || desktopOutputDirDefault.value
      if (info?.lastError) {
        desktopOutputDirError.value = String(info.lastError || '').trim()
      }
      return
    }

    const v = await window.wechatDesktop.getOutputDir()
    desktopOutputDir.value = String(v || '').trim()
    desktopOutputDirDefault.value = desktopOutputDir.value
    desktopOutputDirPending.value = ''
    desktopOutputDirIsDefault.value = true
    desktopOutputDirCanChange.value = false
    desktopOutputDirUnavailableReason.value = '当前桌面环境不支持修改 output 目录'
    desktopOutputDirInput.value = desktopOutputDir.value
  } catch (e) {
    desktopOutputDirError.value = e?.message || '读取 output 目录失败'
  } finally {
    desktopOutputDirLoading.value = false
  }
}

const onDesktopOpenOutputDir = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.openOutputDir) return
  desktopOutputDirLoading.value = true
  desktopOutputDirError.value = ''
  try {
    const res = await window.wechatDesktop.openOutputDir()
    if (res?.path) desktopOutputDir.value = String(res.path || '').trim()
  } catch (e) {
    desktopOutputDirError.value = e?.message || '打开 output 目录失败'
  } finally {
    desktopOutputDirLoading.value = false
  }
}

const onDesktopChooseOutputDir = async () => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.chooseDirectory) return
  desktopOutputDirError.value = ''
  desktopOutputDirMessage.value = ''
  try {
    const result = await window.wechatDesktop.chooseDirectory({ title: '选择新的 output 目录' })
    if (result && !result.canceled && Array.isArray(result.filePaths) && result.filePaths.length > 0) {
      desktopOutputDirInput.value = String(result.filePaths[0] || '').trim()
    }
  } catch (e) {
    desktopOutputDirError.value = e?.message || '选择 output 目录失败'
  }
}

const applyDesktopOutputDir = async (nextDir) => {
  if (!process.client || typeof window === 'undefined') return
  if (!window.wechatDesktop?.setOutputDir) {
    desktopOutputDirError.value = '当前桌面环境不支持修改 output 目录'
    return
  }
  if (!desktopOutputDirCanChange.value) {
    desktopOutputDirError.value = desktopOutputDirUnavailableReason.value || '当前环境不支持修改 output 目录'
    return
  }
  desktopOutputDirApplying.value = true
  desktopOutputDirError.value = ''
  desktopOutputDirMessage.value = ''
  desktopOutputDirProgress.value = null
  try {
    const res = await window.wechatDesktop.setOutputDir(String(nextDir ?? '').trim())
    if (res?.success === false) {
      desktopOutputDirError.value = String(res?.error || '修改 output 目录失败').trim()
      await refreshDesktopOutputDir()
      return
    }
    await refreshDesktopOutputDir()
    desktopOutputDirMessage.value = String(
      res?.message || (res?.changed === false ? 'output 目录未变化' : 'output 目录已更新')
    ).trim()
  } catch (e) {
    desktopOutputDirError.value = e?.message || '修改 output 目录失败'
    await refreshDesktopOutputDir()
  } finally {
    desktopOutputDirApplying.value = false
  }
}

const onDesktopOutputDirApply = async () => {
  await applyDesktopOutputDir(desktopOutputDirInput.value)
}

const onDesktopOutputDirReset = async () => {
  desktopOutputDirInput.value = desktopOutputDirDefault.value
  await applyDesktopOutputDir('')
}

const refreshBackendLogFileInfo = async () => {
  if (!process.client || typeof window === 'undefined') return
  desktopLogFileLoading.value = true
  desktopLogFileError.value = ''
  try {
    const resp = await fetchAdminEndpoint('/admin/log-file')
    desktopLogFilePath.value = String(resp?.path || '').trim()
  } catch (e) {
    desktopLogFileError.value = e?.message || '读取日志文件失败'
  } finally {
    desktopLogFileLoading.value = false
  }
}

const onOpenBackendLogFile = async () => {
  if (!process.client || typeof window === 'undefined') return
  desktopLogFileOpening.value = true
  desktopLogFileError.value = ''
  try {
    const resp = await fetchAdminEndpoint('/admin/log-file/open', { method: 'POST' })
    if (resp?.path) desktopLogFilePath.value = String(resp.path || '').trim()
  } catch (e) {
    desktopLogFileError.value = e?.message || '打开日志文件失败'
  } finally {
    desktopLogFileOpening.value = false
  }
}

const applyDesktopBackendPort = async () => {
  if (!process.client || typeof window === 'undefined') return
  const raw = String(desktopBackendPortInput.value || '').trim()
  const n = Number(raw)
  if (!Number.isInteger(n) || n < 1 || n > 65535) {
    desktopBackendPortError.value = '端口无效：请输入 1-65535 的整数'
    return
  }
  desktopBackendPortApplying.value = true
  desktopBackendPortError.value = ''
  try {
    if (window.wechatDesktop?.setBackendPort) {
      await window.wechatDesktop.setBackendPort(n)
      return
    }

    let currentBackendPort = null
    try {
      const info = await fetchAdminEndpoint('/admin/port')
      const p = Number(info?.port)
      if (Number.isInteger(p) && p >= 1 && p <= 65535) currentBackendPort = p
    } catch {}
    const uiPort = (() => {
      const rawPort = String(window.location?.port || '').trim()
      if (rawPort) return Number(rawPort)
      return window.location?.protocol === 'https:' ? 443 : 80
    })()
    const isUiServedByBackend = !!(currentBackendPort && uiPort === currentBackendPort)

    await fetchAdminEndpoint('/admin/port', {
      method: 'POST',
      body: { port: n },
    })

    let protocol = String(window.location?.protocol || 'http:')
    if (protocol !== 'http:' && protocol !== 'https:') protocol = 'http:'
    const host = String(window.location?.hostname || '').trim() || '127.0.0.1'
    const nextOrigin = `${protocol}//${host}:${n}`
    writeApiBaseOverride(`${nextOrigin}/api`)
    invalidateApiBaseCache()

    const waitForHealth = async (healthUrl, timeoutMs = 30_000) => {
      const startedAt = Date.now()
      while (true) {
        try {
          const r = await fetch(healthUrl, { method: 'GET' })
          if (r && r.status < 500) return
        } catch {}
        if (Date.now() - startedAt > timeoutMs) throw new Error(`后端启动超时：${healthUrl}`)
        await new Promise((r) => setTimeout(r, 300))
      }
    }
    await waitForHealth(`${nextOrigin}/api/health`, 30_000)

    if (isUiServedByBackend) {
      const nextUrl = new URL(window.location.href)
      nextUrl.port = String(n)
      window.location.href = nextUrl.toString()
      return
    }

    try {
      window.location.reload()
    } catch {}
  } catch (e) {
    desktopBackendPortError.value = e?.message || '设置后端端口失败（若为网页端，请确认后端为本机启动且允许重启）'
    await refreshDesktopBackendPort()
  } finally {
    desktopBackendPortApplying.value = false
  }
}

const toggleDesktopAutoLaunch = async () => {
  if (!isDesktopEnv.value || desktopAutoLaunchLoading.value) return
  await setDesktopAutoLaunch(!desktopAutoLaunch.value)
}

const onDesktopCloseBehaviorChange = async (ev) => {
  const v = String(ev?.target?.value || '').trim()
  await setDesktopCloseBehavior(v)
}

const onDesktopBackendPortApply = async () => {
  await applyDesktopBackendPort()
}

const onDesktopBackendPortReset = async () => {
  desktopBackendPortInput.value = String(desktopBackendPortDefault.value || 10392)
  await applyDesktopBackendPort()
}

const toggleDesktopAutoRealtime = () => {
  const next = !desktopAutoRealtime.value
  desktopAutoRealtime.value = next
  writeLocalBoolSetting(DESKTOP_SETTING_AUTO_REALTIME_KEY, next)
}

const toggleDesktopDefaultToChat = () => {
  const next = !desktopDefaultToChatWhenData.value
  desktopDefaultToChatWhenData.value = next
  writeLocalBoolSetting(DESKTOP_SETTING_DEFAULT_TO_CHAT_KEY, next)
}

const toggleSnsUseCache = () => {
  const next = !snsUseCache.value
  snsUseCache.value = next
  writeLocalBoolSetting(SNS_SETTING_USE_CACHE_KEY, next)
}

const onDesktopCheckUpdates = async () => {
  await desktopUpdate.manualCheck()
}

watch(() => props.open, async (isOpen) => {
  if (!isOpen) return
  await chatAccounts.ensureLoaded()
  await refreshBackendLogFileInfo()
  await refreshKeywordMonitorAll()
  if (isDesktopEnv.value) {
    await refreshDesktopOutputDir()
    await refreshDesktopOutputDirProgress()
  }
  await scrollToTargetSection()
}, { immediate: true })

watch(targetSection, async () => {
  if (!props.open) return
  await scrollToTargetSection()
})

watch(selectedAccount, async () => {
  if (!props.open) return
  await refreshKeywordMonitorAll()
})

onMounted(async () => {
  if (process.client && typeof window !== 'undefined') {
    const isElectron = /electron/i.test(String(navigator.userAgent || ''))
    isDesktopEnv.value = isElectron && !!window.wechatDesktop
    window.addEventListener('keydown', onEscKeydown)
    if (window.wechatDesktop?.onOutputDirChangeProgress) {
      removeDesktopOutputDirProgressListener = window.wechatDesktop.onOutputDirChangeProgress((progress) => {
        applyDesktopOutputDirProgress(progress)
      })
    }
  }

  desktopAutoRealtime.value = readLocalBoolSetting(DESKTOP_SETTING_AUTO_REALTIME_KEY, false)
  desktopDefaultToChatWhenData.value = readLocalBoolSetting(DESKTOP_SETTING_DEFAULT_TO_CHAT_KEY, false)
  snsUseCache.value = readLocalBoolSetting(SNS_SETTING_USE_CACHE_KEY, true)
  privacyStore.init()

  await refreshDesktopBackendPort()
  if (isDesktopEnv.value) {
    void desktopUpdate.initListeners()
    await refreshDesktopAutoLaunch()
    await refreshDesktopCloseBehavior()
    await refreshDesktopOutputDir()
    await refreshDesktopOutputDirProgress()
  }

  await nextTick()
  onContentScroll()
})

onBeforeUnmount(() => {
  if (!process.client || typeof window === 'undefined') return
  window.removeEventListener('keydown', onEscKeydown)
  if (typeof removeDesktopOutputDirProgressListener === 'function') {
    removeDesktopOutputDirProgressListener()
    removeDesktopOutputDirProgressListener = null
  }
})
</script>

<style scoped>
.settings-switch {
  width: 44px;
  height: 24px;
  border-radius: 999px;
  padding: 2px;
  transition: background-color 0.16s ease, opacity 0.16s ease, filter 0.16s ease;
}

.settings-switch-thumb {
  display: block;
  height: 20px;
  width: 20px;
  border-radius: 999px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.24);
  transition: transform 0.16s ease;
}

/* 自定义右侧滚动条 */
.scrollbar-custom::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.scrollbar-custom::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-custom::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 8px;
}
.scrollbar-custom::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}
</style>
