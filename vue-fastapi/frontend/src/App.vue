<template>
  <el-container class="app-container">
    <!-- 侧边栏：API Key 输入 -->
    <el-aside width="300px" class="sidebar">
      <h3>设置</h3>
      <el-input
        v-model="apiKey"
        type="password"
        placeholder="请输入 DeepSeek API Key"
        show-password
        clearable
      />
      <p class="tip">
        <a href="https://platform.deepseek.com/transactions" target="_blank">获取 API Key</a>
      </p>
    </el-aside>

    <!-- 主区域 -->
    <el-main>
      <h2>AI 智能 PDF 问答工具</h2>

      <!-- 文件上传 -->
      <el-upload
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        accept=".pdf"
        :limit="1"
      >
        <el-button type="primary">上传 PDF 文件</el-button>
        <template #tip>
          <div class="el-upload__tip">只能上传 PDF 文件，上传后立即解析</div>
        </template>
      </el-upload>

      <!-- 聊天记录展示区 -->
      <div class="chat-area" ref="chatArea">
        <div v-if="messages.length === 0" class="empty-tip">
          上传文档后开始提问吧
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message"
          :class="msg.role === 'user' ? 'user-msg' : 'ai-msg'"
        >
          <div class="bubble">{{ msg.content }}</div>
        </div>
        <div v-if="loading" class="loading-tip">
          <el-icon class="is-loading"><Loading /></el-icon>
          AI 正在思考...
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="question"
          placeholder="对 PDF 的内容进行提问"
          :disabled="!documentId || loading"
          @keyup.enter="sendQuestion"
        />
        <el-button
          type="primary"
          :disabled="!documentId || !question.trim() || loading"
          :loading="loading"
          @click="sendQuestion"
        >
          发送
        </el-button>
      </div>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const apiKey = ref('')
const documentId = ref(null)
const question = ref('')
const messages = ref([])          // 聊天历史，格式: [{role:'user'|'assistant', content:string}]
const loading = ref(false)
const fileList = ref([])
const chatArea = ref(null)

// 处理文件选择
const handleFileChange = async (uploadFile) => {
  if (!apiKey.value) {
    ElMessage.warning('请先输入 API Key')
    return
  }
  const formData = new FormData()
  formData.append('file', uploadFile.raw)

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    })
    const data = await res.json()
    if (data.document_id) {
      documentId.value = data.document_id
      ElMessage.success(`文件 "${data.filename}" 上传成功，可以开始提问`)
      // 清空历史消息，因为换文档了
      messages.value = []
    } else {
      ElMessage.error(data.detail || data.error || '上传失败')
      fileList.value = []   // 移除失败文件
    }
  } catch (e) {
    ElMessage.error('网络错误，上传失败')
    fileList.value = []
  }
}

const handleFileRemove = () => {
  documentId.value = null
  messages.value = []
}

// 发送问题
const sendQuestion = async () => {
  if (!apiKey.value) {
    ElMessage.warning('请先输入 API Key')
    return
  }
  if (!documentId.value) {
    ElMessage.warning('请先上传 PDF')
    return
  }
  const q = question.value.trim()
  if (!q) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: q })
  question.value = ''
  loading.value = true
  scrollToBottom()

  // 添加一个空的 AI 消息占位，后续流式填充
  const aiMsg = { role: 'assistant', content: '' }
  messages.value.push(aiMsg)
  const aiIndex = messages.value.length - 1

  const requestBody = {
    api_key: apiKey.value,
    document_id: documentId.value,
    question: q,
    history: messages.value.slice(0, -2)  // 去掉刚添加的 user 和 空 ai，发送之前的完整历史
  }

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok || !response.body) {
      throw new Error('请求失败')
    }

    // 使用 fetch 读取 SSE 流
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // 按 \n\n 分割事件
      const events = buffer.split('\n\n')
      buffer = events.pop()  // 最后一个可能不完整，保留

      for (const event of events) {
        if (event.startsWith('data: ')) {
          const jsonStr = event.slice(6)
          try {
            const data = JSON.parse(jsonStr)
            if (data.type === 'chunk') {
              messages.value[aiIndex].content += data.content
              scrollToBottom()
            } else if (data.type === 'done') {
              // 完成
            } else if (data.type === 'error') {
              messages.value[aiIndex].content = '发生错误：' + data.content
            }
          } catch (e) {
            console.error('解析 SSE 数据失败', e)
          }
        }
      }
    }
    // 处理完所有流后，如果最后还有内容，也加入
    if (buffer.startsWith('data: ')) {
      const jsonStr = buffer.slice(6)
      try {
        const data = JSON.parse(jsonStr)
        if (data.type === 'chunk') {
          messages.value[aiIndex].content += data.content
        }
      } catch {}
    }
  } catch (e) {
    messages.value[aiIndex].content = '请求出错：' + e.message
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 自动滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}
.sidebar {
  background: #f5f7fa;
  padding: 20px;
  border-right: 1px solid #e4e7ed;
}
.tip {
  font-size: 12px;
  margin-top: 10px;
}
.chat-area {
  height: calc(100vh - 250px);
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  margin: 20px 0;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty-tip {
  color: #909399;
  text-align: center;
  margin-top: 40px;
}
.message {
  display: flex;
}
.user-msg {
  justify-content: flex-end;
}
.ai-msg {
  justify-content: flex-start;
}
.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
.user-msg .bubble {
  background: #409eff;
  color: white;
}
.ai-msg .bubble {
  background: #f0f2f5;
  color: #303133;
}
.loading-tip {
  color: #909399;
  display: flex;
  align-items: center;
  gap: 6px;
}
.input-area {
  display: flex;
  gap: 10px;
}
</style>
