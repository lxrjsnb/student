<template>
  <section class="page">
    <header class="hero">
      <div class="heroTop">
        <div class="avatar" aria-hidden="true">
          <img v-if="user?.avatar" class="avatarImg" :src="user.avatar" alt="头像" />
          <span v-else>{{ displayInitial }}</span>
        </div>

        <div class="heroCopy">
          <p class="eyebrow">Profile</p>
          <h2 class="title">
            {{ user?.nickname || user?.username }}
            <span class="roleInline">{{ roleText }}</span>
          </h2>
          <p class="subtitle">{{ studentNoText }}</p>
        </div>
      </div>

      <div class="heroMeta">
        <span class="metaPill">phone {{ phoneText }}</span>
        <span class="metaPill">department {{ departmentText }}</span>
      </div>
    </header>

    <section class="panel">
      <div class="panelHead">
        <div>
          <p class="panelKicker">Workspace</p>
          <h3 class="panelTitle">我的</h3>
        </div>
      </div>

      <div class="actionList">
        <button class="actionRow" type="button" @click="$emit('openSettings')">
          <div class="actionMain">
            <span class="actionTitle">账户设置</span>
            <span class="actionDesc">修改手机号和密码</span>
          </div>
          <span class="actionArrow" aria-hidden="true">›</span>
        </button>

        <button v-if="canDelegate" class="actionRow" type="button" @click="$emit('openDelegation')">
          <div class="actionMain">
            <span class="actionTitle actionTitle--with-dot">
              {{ delegationLabel }}
              <span v-if="delegationAlert" class="alertDot" aria-hidden="true"></span>
            </span>
            <span class="actionDesc">{{ delegationDesc }}</span>
          </div>
          <span class="actionArrow" aria-hidden="true">›</span>
        </button>

        <button v-if="canOpenDeveloperAccess" class="actionRow" type="button" @click="$emit('openDeveloperAccess')">
          <div class="actionMain">
            <span class="actionTitle">开发者权限</span>
            <span class="actionDesc">进入表格页直接编辑全部用户信息</span>
          </div>
          <span class="actionArrow" aria-hidden="true">›</span>
        </button>

        <button class="actionRow actionRow--danger" type="button" @click="$emit('logout')">
          <div class="actionMain">
            <span class="actionTitle">退出登录</span>
            <span class="actionDesc">清除当前登录状态并返回登录页</span>
          </div>
          <span class="actionState actionState--danger">退出</span>
        </button>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: null },
  delegationAlert: { type: Boolean, default: false }
})

defineEmits(['logout', 'openSettings', 'openDelegation', 'openDeveloperAccess'])

const displayInitial = computed(() => {
  const value = props.user?.nickname || props.user?.username || '?'
  return String(value).charAt(0).toUpperCase()
})

const roleText = computed(() => {
  if (props.user?.isTemporarySuperAdmin && props.user?.baseRole === 'admin') return '部长 · 临时主席'
  if (props.user?.role === 'super_admin') return '主席'
  if (props.user?.role === 'admin') return '部长'
  return '部员'
})

const canDelegate = computed(() => {
  if (props.user?.baseRole === 'super_admin') return true
  if (props.user?.baseRole === 'admin') return !props.user?.isTemporarySuperAdmin
  return false
})
const canOpenDeveloperAccess = computed(() => props.user?.baseRole === 'super_admin')
const delegationLabel = computed(() => (props.user?.baseRole === 'super_admin' ? '放权' : '权限申请'))
const delegationDesc = computed(() => (props.user?.baseRole === 'super_admin' ? '进入独立页面管理临时主席权限' : '填写理由后提交给主席审批'))
const phoneText = computed(() => props.user?.phone || '-')
const departmentText = computed(() => props.user?.department || '-')
const studentNoText = computed(() => props.user?.studentNo || '-')
</script>

<style scoped>
.page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 18px 120px;
}

.hero {
  padding: 24px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 22px 54px rgba(20, 29, 41, 0.08);
}

.heroTop {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 78px;
  height: 78px;
  border-radius: 24px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #e2c58f, #b78b4a);
  color: #152131;
  font-size: 28px;
  font-weight: 900;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
}

.avatarImg {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.heroCopy {
  min-width: 0;
}

.eyebrow,
.panelKicker {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(24, 59, 77, 0.54);
}

.title {
  margin: 8px 0 0;
  font-size: clamp(30px, 4vw, 46px);
  line-height: 1;
  letter-spacing: -0.05em;
  color: #152131;
}

.roleInline {
  margin-left: 10px;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: rgba(24, 59, 77, 0.64);
}

.subtitle {
  margin: 8px 0 0;
  color: rgba(24, 33, 47, 0.62);
  font-size: 14px;
}

.heroMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.metaPill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(24, 59, 77, 0.08);
  color: #183b4d;
  font-size: 12px;
  font-weight: 700;
}

.panel {
  margin-top: 18px;
  padding: 22px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(24, 33, 47, 0.08);
  box-shadow: 0 20px 48px rgba(20, 29, 41, 0.06);
}

.panelHead {
  margin-bottom: 16px;
}

.panelTitle {
  margin: 8px 0 0;
  font-size: 30px;
  line-height: 1.04;
  letter-spacing: -0.05em;
  color: #152131;
}

.actionList {
  display: grid;
  gap: 10px;
}

.actionRow {
  width: 100%;
  border: 0;
  border-radius: 22px;
  padding: 16px 18px;
  background: rgba(248, 242, 231, 0.66);
  border: 1px solid rgba(24, 33, 47, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  text-align: left;
  transition: transform 0.16s ease, background 0.16s ease;
}

.actionRow:hover {
  transform: translateY(-1px);
  background: rgba(248, 242, 231, 0.88);
}

.actionRow--danger {
  background: rgba(154, 47, 39, 0.08);
  border-color: rgba(154, 47, 39, 0.08);
}

.actionMain {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.actionTitle {
  font-size: 16px;
  font-weight: 800;
  color: #152131;
}

.actionTitle--with-dot {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.alertDot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #d83b32;
  box-shadow: 0 0 0 4px rgba(216, 59, 50, 0.12);
}

.actionDesc {
  color: rgba(24, 33, 47, 0.62);
  font-size: 13px;
  line-height: 1.6;
}

.actionArrow,
.actionState {
  flex-shrink: 0;
  font-size: 22px;
  line-height: 1;
  color: rgba(24, 59, 77, 0.4);
}

.actionState {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.actionState--danger {
  color: #9a2f27;
}

@media (max-width: 768px) {
  .page {
    padding: 20px 14px 120px;
  }

  .hero {
    padding: 18px;
    border-radius: 26px;
  }

  .heroTop {
    align-items: flex-start;
    gap: 12px;
  }

  .avatar {
    width: 64px;
    height: 64px;
    border-radius: 20px;
    font-size: 24px;
  }

  .title {
    font-size: 32px;
  }

  .roleInline {
    display: inline-block;
    margin: 8px 0 0;
    font-size: 13px;
  }

  .panel {
    padding: 18px;
    border-radius: 24px;
  }

  .panelTitle {
    font-size: 26px;
  }

  .actionRow {
    border-radius: 20px;
    padding: 15px 16px;
  }
}
</style>
