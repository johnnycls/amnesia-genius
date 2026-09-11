import i18n from 'i18next';
import { initReactI18next, useTranslation } from 'react-i18next';

export const localeOptions = [
  { code: 'en', name: 'English' },
  { code: 'zh-CN', name: '简体中文' },
  { code: 'zh-TW', name: '繁體中文' },
  { code: 'ja', name: '日本語' },
  { code: 'ko', name: '한국어' },
] as const;

export type Locale = (typeof localeOptions)[number]['code'];

const english = {
  appName: 'Amnesia Agent',
  chat: 'Chat', workspace: 'Workspace', history: 'History', settings: 'Settings',
  serverReady: 'Server ready', serverStarting: 'Starting server', serverError: 'Server error', serverStopped: 'Server stopped',
  toggleSidebar: 'Toggle sidebar', openMenu: 'Open menu', closeMenu: 'Close menu', language: 'Language',
  startConversation: 'Start a conversation', startConversationHint: 'Ask the local agent to inspect, explain, or change something in your workspace.',
  messagePlaceholder: 'Message the local agent…', waitingForServer: 'Waiting for the local server…',
  send: 'Send', stop: 'Stop', enterToSend: 'Enter to send · Shift+Enter for a new line',
  you: 'You', agent: 'Agent', streaming: 'Streaming', toolCall: 'Agent requested a tool call', toolResult: 'Tool result',
  systemPrompt: 'System prompt', systemPromptHint: 'The instructions that shape every agent turn.', memory: 'Memory', memoryHint: 'Persistent notes available to the agent in its workspace.',
  save: 'Save', reset: 'Reset', saved: 'saved', resetDone: 'reset',
  savedDays: 'Saved days', clearHistory: 'Clear history', noHistory: 'No saved history yet.', chooseSavedDay: 'Choose a saved day',
  historyHint: 'Select a date to inspect the persisted conversation without changing the live chat.', readOnlyHistory: 'Read-only history inspection',
  provider: 'Provider', providerHint: 'The API key is write-only. Leave it blank to keep the currently stored key.', model: 'Model', apiKey: 'API key', keepCurrentKey: 'Leave blank to keep current', baseUrl: 'Base URL',
  providerParams: 'Provider params (JSON object)', executionLimits: 'Execution limits', executionHint: 'These limits apply to the local agent’s command execution and context.',
  commandTimeout: 'Command timeout (seconds)', maxOutput: 'Max output bytes', maxContext: 'Max context characters', restoreDefaults: 'Restore defaults',
  settingsSaved: 'Settings saved. The next turn will use the new session configuration.', settingsRestored: 'Settings restored.', cancelled: 'Turn cancelled.',
  savedMessage: '{{name}} saved.', resetMessage: '{{name}} reset.', invalidJson: 'Provider params must be valid JSON.', positiveNumber: '{{label}} must be a positive number.', positiveInteger: '{{label}} must be a positive integer.',
  clearHistoryConfirm: 'Clear all persisted daily history? This cannot be undone.', resetConfirm: 'Reset {{name}} to its packaged default?',
  dismiss: 'Dismiss', clear: 'Clear', switchLanguage: 'Switch language',
};

const translations: Record<Locale, typeof english> = {
  en: english,
  'zh-CN': { ...english, appName: 'Amnesia Agent', chat: '聊天', workspace: '工作区', history: '历史', settings: '设置', serverReady: '服务器已就绪', serverStarting: '正在启动服务器', serverError: '服务器错误', serverStopped: '服务器已停止', toggleSidebar: '切换侧边栏', openMenu: '打开菜单', closeMenu: '关闭菜单', language: '语言', startConversation: '开始对话', startConversationHint: '让本地智能体检查、解释或修改你的工作区。', messagePlaceholder: '给本地智能体发送消息…', waitingForServer: '正在等待本地服务器…', send: '发送', stop: '停止', enterToSend: '按 Enter 发送 · Shift+Enter 换行', you: '你', agent: '智能体', streaming: '正在生成', toolCall: '智能体请求执行工具', toolResult: '工具结果', systemPrompt: '系统提示词', systemPromptHint: '影响每次智能体对话的指令。', memory: '记忆', memoryHint: '智能体在工作区中可以读取的持久笔记。', save: '保存', reset: '重置', saved: '已保存', resetDone: '已重置', savedDays: '保存的日期', clearHistory: '清除历史', noHistory: '还没有保存的历史记录。', chooseSavedDay: '选择保存的日期', historyHint: '选择日期查看历史对话，不会改变当前聊天。', readOnlyHistory: '只读历史记录', provider: '提供商', providerHint: 'API 密钥仅可写入。留空以保留当前密钥。', model: '模型', apiKey: 'API 密钥', keepCurrentKey: '留空以保留当前密钥', baseUrl: '基础 URL', providerParams: '提供商参数（JSON 对象）', executionLimits: '执行限制', executionHint: '这些限制作用于本地智能体的命令执行和上下文。', commandTimeout: '命令超时（秒）', maxOutput: '最大输出字节数', maxContext: '最大上下文字符数', restoreDefaults: '恢复默认设置', settingsSaved: '设置已保存。下一次对话将使用新的会话配置。', settingsRestored: '设置已恢复。', cancelled: '对话已取消。', savedMessage: '{{name}}已保存。', resetMessage: '{{name}}已重置。', clearHistoryConfirm: '清除所有每日历史记录？此操作无法撤销。', resetConfirm: '将{{name}}恢复为打包时的默认值？', dismiss: '关闭提示', clear: '清除', switchLanguage: '切换语言' },
  'zh-TW': { ...english, appName: 'Amnesia Agent', chat: '聊天', workspace: '工作區', history: '歷史', settings: '設定', serverReady: '伺服器已就緒', serverStarting: '正在啟動伺服器', serverError: '伺服器錯誤', serverStopped: '伺服器已停止', toggleSidebar: '切換側邊欄', openMenu: '開啟選單', closeMenu: '關閉選單', language: '語言', startConversation: '開始對話', startConversationHint: '讓本地代理檢查、解釋或修改你的工作區。', messagePlaceholder: '傳送訊息給本地代理…', waitingForServer: '正在等待本地伺服器…', send: '傳送', stop: '停止', enterToSend: '按 Enter 傳送 · Shift+Enter 換行', you: '你', agent: '代理', streaming: '正在產生', toolCall: '代理要求執行工具', toolResult: '工具結果', systemPrompt: '系統提示詞', systemPromptHint: '影響每次代理對話的指令。', memory: '記憶', memoryHint: '代理在工作區中可以讀取的持久筆記。', save: '儲存', reset: '重設', saved: '已儲存', resetDone: '已重設', savedDays: '儲存的日期', clearHistory: '清除歷史', noHistory: '尚未有儲存的歷史記錄。', chooseSavedDay: '選擇儲存的日期', historyHint: '選擇日期查看歷史對話，不會改變目前聊天。', readOnlyHistory: '唯讀歷史記錄', provider: '提供商', providerHint: 'API 金鑰僅可寫入。留白以保留目前金鑰。', model: '模型', apiKey: 'API 金鑰', keepCurrentKey: '留白以保留目前金鑰', baseUrl: '基礎 URL', providerParams: '提供商參數（JSON 物件）', executionLimits: '執行限制', executionHint: '這些限制作用於本地代理的命令執行和上下文。', commandTimeout: '命令逾時（秒）', maxOutput: '最大輸出位元組數', maxContext: '最大上下文字元數', restoreDefaults: '恢復預設設定', settingsSaved: '設定已儲存。下一次對話將使用新的工作階段設定。', settingsRestored: '設定已恢復。', cancelled: '對話已取消。', savedMessage: '{{name}}已儲存。', resetMessage: '{{name}}已重設。', clearHistoryConfirm: '清除所有每日歷史記錄？此操作無法復原。', resetConfirm: '將{{name}}恢復為打包時的預設值？', dismiss: '關閉提示', clear: '清除', switchLanguage: '切換語言' },
  ja: { ...english, appName: 'Amnesia Agent', chat: 'チャット', workspace: 'ワークスペース', history: '履歴', settings: '設定', serverReady: 'サーバー準備完了', serverStarting: 'サーバーを起動中', serverError: 'サーバーエラー', serverStopped: 'サーバー停止', toggleSidebar: 'サイドバーを切り替え', openMenu: 'メニューを開く', closeMenu: 'メニューを閉じる', language: '言語', startConversation: '会話を始める', startConversationHint: 'ローカルエージェントにワークスペースの確認、説明、変更を依頼できます。', messagePlaceholder: 'ローカルエージェントにメッセージ…', waitingForServer: 'ローカルサーバーを待機中…', send: '送信', stop: '停止', enterToSend: 'Enterで送信 · Shift+Enterで改行', you: 'あなた', agent: 'エージェント', streaming: '生成中', toolCall: 'エージェントがツールを要求しました', toolResult: 'ツール結果', systemPrompt: 'システムプロンプト', systemPromptHint: 'すべてのエージェントターンに適用される指示。', memory: 'メモリ', memoryHint: 'ワークスペースでエージェントが参照する永続メモ。', save: '保存', reset: 'リセット', saved: '保存済み', resetDone: 'リセット済み', savedDays: '保存された日付', clearHistory: '履歴を消去', noHistory: '保存された履歴はありません。', chooseSavedDay: '日付を選択', historyHint: '日付を選ぶと現在のチャットを変えずに履歴を確認できます。', readOnlyHistory: '読み取り専用の履歴', provider: 'プロバイダー', providerHint: 'APIキーは書き込み専用です。空欄にすると現在のキーを保持します。', model: 'モデル', apiKey: 'APIキー', keepCurrentKey: '現在のキーを保持するには空欄', baseUrl: 'ベースURL', providerParams: 'プロバイダーパラメータ（JSONオブジェクト）', executionLimits: '実行制限', executionHint: 'ローカルエージェントのコマンド実行とコンテキストに適用されます。', commandTimeout: 'コマンドタイムアウト（秒）', maxOutput: '最大出力バイト', maxContext: '最大コンテキスト文字数', restoreDefaults: 'デフォルトに戻す', settingsSaved: '設定を保存しました。次のターンから新しいセッション設定を使用します。', settingsRestored: '設定を復元しました。', cancelled: 'ターンをキャンセルしました。', savedMessage: '{{name}}を保存しました。', resetMessage: '{{name}}をリセットしました。', clearHistoryConfirm: '保存された日別履歴をすべて消去しますか？元に戻せません。', resetConfirm: '{{name}}をパッケージのデフォルトに戻しますか？', dismiss: '閉じる', clear: '消去', switchLanguage: '言語を切り替え' },
  ko: { ...english, appName: 'Amnesia Agent', chat: '채팅', workspace: '워크스페이스', history: '기록', settings: '설정', serverReady: '서버 준비 완료', serverStarting: '서버 시작 중', serverError: '서버 오류', serverStopped: '서버 중지됨', toggleSidebar: '사이드바 전환', openMenu: '메뉴 열기', closeMenu: '메뉴 닫기', language: '언어', startConversation: '대화 시작', startConversationHint: '로컬 에이전트에게 워크스페이스를 확인, 설명 또는 변경하도록 요청하세요.', messagePlaceholder: '로컬 에이전트에 메시지…', waitingForServer: '로컬 서버를 기다리는 중…', send: '보내기', stop: '중지', enterToSend: 'Enter로 보내기 · Shift+Enter로 줄바꿈', you: '나', agent: '에이전트', streaming: '생성 중', toolCall: '에이전트가 도구를 요청했습니다', toolResult: '도구 결과', systemPrompt: '시스템 프롬프트', systemPromptHint: '모든 에이전트 턴에 적용되는 지침입니다.', memory: '메모리', memoryHint: '워크스페이스에서 에이전트가 참조하는 영구 메모입니다.', save: '저장', reset: '초기화', saved: '저장됨', resetDone: '초기화됨', savedDays: '저장된 날짜', clearHistory: '기록 삭제', noHistory: '저장된 기록이 없습니다.', chooseSavedDay: '날짜 선택', historyHint: '날짜를 선택하면 현재 채팅을 바꾸지 않고 기록을 확인할 수 있습니다.', readOnlyHistory: '읽기 전용 기록', provider: '제공자', providerHint: 'API 키는 쓰기 전용입니다. 비워 두면 현재 키를 유지합니다.', model: '모델', apiKey: 'API 키', keepCurrentKey: '현재 키를 유지하려면 비워 두세요', baseUrl: '기본 URL', providerParams: '제공자 매개변수（JSON 객체）', executionLimits: '실행 제한', executionHint: '로컬 에이전트의 명령 실행과 컨텍스트에 적용됩니다.', commandTimeout: '명령 시간 제한（초）', maxOutput: '최대 출력 바이트', maxContext: '최대 컨텍스트 문자', restoreDefaults: '기본값 복원', settingsSaved: '설정이 저장되었습니다. 다음 턴부터 새 세션 설정을 사용합니다.', settingsRestored: '설정이 복원되었습니다.', cancelled: '턴이 취소되었습니다.', savedMessage: '{{name}}이(가) 저장되었습니다.', resetMessage: '{{name}}이(가) 초기화되었습니다.', clearHistoryConfirm: '저장된 일일 기록을 모두 삭제할까요? 되돌릴 수 없습니다.', resetConfirm: '{{name}}을(를) 패키지 기본값으로 초기화할까요?', dismiss: '닫기', clear: '삭제', switchLanguage: '언어 전환' },
};

const storedLocale = typeof localStorage === 'undefined' ? null : localStorage.getItem('amnesia.locale') as Locale | null;
const initialLocale = localeOptions.some((option) => option.code === storedLocale) ? storedLocale! : 'en';

i18n.use(initReactI18next).init({ resources: Object.fromEntries(localeOptions.map(({ code }) => [code, { translation: translations[code] }])), lng: initialLocale, fallbackLng: 'en', interpolation: { escapeValue: false } });

export function setLocale(locale: Locale): void {
  if (typeof localStorage !== 'undefined') localStorage.setItem('amnesia.locale', locale);
  void i18n.changeLanguage(locale);
}

export function useI18n() {
  const result = useTranslation();
  return { ...result, locale: result.i18n.language as Locale, setLocale };
}

export { i18n };
export default i18n;
