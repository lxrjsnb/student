<template>
  <div class="body">
    <div class="card">
      <!-- 登录区域 -->
      <h2 v-if="!currentUserId">打卡系统 - 登录</h2>
      <div v-if="!currentUserId">
        <div class="form-item">
          <label>用户名</label>
          <input v-model="username" type="text" placeholder="请输入用户名（测试账号：test）">
        </div>
        <div class="form-item">
          <label>密码</label>
          <input v-model="password" type="password" placeholder="请输入密码（测试密码：123456）">
        </div>
        <button @click="login">登录</button>
        <div v-if="loginMsg" :class="['message', loginMsgType]">{{ loginMsg }}</div>
      </div>

      <!-- 打卡和查记录区域（登录成功后显示） -->
      <div v-else>
        <h2>今日打卡</h2>
        <button @click="punchIn" style="margin-bottom: 10px;">立即打卡</button>
        <div v-if="punchMsg" :class="['message', punchMsgType]">{{ punchMsg }}</div>

        <hr style="margin: 20px 0;">
        <button @click="loadRecords" style="background-color: #28a745;">查看打卡记录</button>
        <div v-if="records.length > 0" class="records-list">
          <h4>打卡历史：</h4>
          <ul>
            <li v-for="record in records" :key="record.id">
              打卡时间：{{ record.punch_time }}
            </li>
          </ul>
        </div>
        <div v-else-if="recordsLoaded" style="text-align: center; color: #666; margin-top: 10px;">
          暂无打卡记录
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

// 后端地址（和你原来的一样）
const BASE_URL = 'http://127.0.0.1:5000'

// 响应式数据（代替原来的变量）
const username = ref('')
const password = ref('')
const currentUserId = ref(null)
const loginMsg = ref('')
const loginMsgType = ref('')
const punchMsg = ref('')
const punchMsgType = ref('')
const records = ref([])
const recordsLoaded = ref(false)

// 登录函数
const login = async () => {
  loginMsg.value = ''
  if (!username.value || !password.value) {
    loginMsg.value = '用户名和密码不能为空！'
    loginMsgType.value = 'error'
    return
  }

  try {
    const res = await axios.post(`${BASE_URL}/login`, {
      username: username.value,
      password: password.value
    })
    if (res.data.code === 200) {
      loginMsg.value = res.data.msg
      loginMsgType.value = 'success'
      currentUserId.value = res.data.user_id
    } else {
      loginMsg.value = res.data.msg
      loginMsgType.value = 'error'
    }
  } catch (error) {
    loginMsg.value = `登录失败：${error.message}，请检查后端是否启动！`
    loginMsgType.value = 'error'
    console.error('登录错误：', error)
  }
}

// 打卡函数
const punchIn = async () => {
  punchMsg.value = ''
  if (!currentUserId.value) {
    punchMsg.value = '请先登录后再打卡！'
    punchMsgType.value = 'error'
    return
  }

  try {
    const res = await axios.post(`${BASE_URL}/punch`, {
      user_id: currentUserId.value
    })
    if (res.data.code === 200) {
      punchMsg.value = `${res.data.msg} 打卡时间：${res.data.time}`
      punchMsgType.value = 'success'
    } else {
      punchMsg.value = res.data.msg
      punchMsgType.value = 'error'
    }
  } catch (error) {
    punchMsg.value = `打卡失败：${error.message}`
    punchMsgType.value = 'error'
    console.error('打卡错误：', error)
  }
}

// 加载打卡记录函数
const loadRecords = async () => {
  records.value = []
  recordsLoaded.value = false
  if (!currentUserId.value) return

  try {
    const res = await axios.get(`${BASE_URL}/records/${currentUserId.value}`)
    if (res.data.code === 200) {
      records.value = res.data.data
    }
  } catch (error) {
    console.error('加载记录错误：', error)
  } finally {
    recordsLoaded.value = true
  }
}
</script>

<style scoped>
/* 直接把你原来的CSS复制过来，稍微改改选择器就行 */
.body {
  background-color: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  margin: 0;
  font-family: "微软雅黑", Arial, sans-serif;
}

.card {
  background-color: white;
  width: 100%;
  max-width: 450px;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
}

.form-item {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #007bff;
}

button {
  width: 100%;
  padding: 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #0056b3;
}

.message {
  margin-top: 15px;
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 14px;
}

.success {
  background-color: #d4edda;
  color: #155724;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
}

.records-list {
  margin-top: 15px;
}

.records-list h4 {
  color: #333;
  margin-bottom: 10px;
}

.records-list ul {
  list-style: none;
  padding: 0;
}

.records-list li {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  color: #555;
}
</style>