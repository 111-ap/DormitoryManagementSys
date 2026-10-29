<template>
  <div class="page-shell">
    <PageHeader
      eyebrow="Utilities"
      title="水电管理"
      subtitle="房间水电账户、月度账单、模拟充值和余额流水。"
    >
      <el-button plain @click="excelApi.exportBills()">
        <el-icon><Document /></el-icon>导出账单
      </el-button>
      <el-button v-if="!auth.isStudent" type="primary" @click="openBill">
        <el-icon><Plus /></el-icon>生成账单
      </el-button>
    </PageHeader>

    <div class="utility-summary">
      <div class="summary-main">
        <div class="summary-icon"><el-icon><Wallet /></el-icon></div>
        <div>
          <div class="summary-label">账户总余额</div>
          <div class="summary-value">{{ formatMoney(totalBalance) }}</div>
        </div>
      </div>
      <div class="summary-item">
        <span>未缴账单</span>
        <strong>{{ unpaidCount }} 笔</strong>
      </div>
      <div class="summary-item">
        <span>本月充值</span>
        <strong>{{ formatMoney(monthRecharge) }}</strong>
      </div>
    </div>

    <div class="panel panel-pad">
      <el-tabs v-model="tab" @tab-change="loadTab">
        <el-tab-pane label="水电账户" name="accounts">
          <el-table v-loading="loading.accounts" :data="accounts">
            <el-table-column label="房间" min-width="160">
              <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
            </el-table-column>
            <el-table-column label="当前余额" width="140">
              <template #default="{ row }">
                <span class="mono balance-text">{{ formatMoney(row.balance) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }"><StatusTag :value="row.status" /></template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openRecharge(row)">充值</el-button>
                <el-button link type="primary" @click="openTransactions(row)">流水</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="水电账单" name="bills">
          <el-table v-loading="loading.bills" :data="bills">
            <el-table-column label="房间" min-width="150">
              <template #default="{ row }">{{ row.building_name }} · {{ row.room_no }}</template>
            </el-table-column>
            <el-table-column label="月份" width="95">
              <template #default="{ row }">{{ row.bill_month?.slice(0, 7) }}</template>
            </el-table-column>
            <el-table-column label="用水 / 水费" width="130">
              <template #default="{ row }">{{ row.water_usage ?? 0 }} / {{ formatMoney(row.water_amount) }}</template>
            </el-table-column>
            <el-table-column label="用电 / 电费" width="140">
              <template #default="{ row }">{{ row.electricity_usage ?? 0 }} / {{ formatMoney(row.electricity_amount) }}</template>
            </el-table-column>
            <el-table-column label="合计" width="110">
              <template #default="{ row }"><strong>{{ formatMoney(row.total_amount) }}</strong></template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }"><StatusTag :value="row.status" /></template>
            </el-table-column>
            <el-table-column label="缴费时间" min-width="160">
              <template #default="{ row }">{{ formatDateTime(row.paid_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'unpaid'" link type="success" @click="payBill(row)">缴费</el-button>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="充值记录" name="recharges">
          <el-table v-loading="loading.recharges" :data="recharges">
            <el-table-column prop="order_no" label="订单号" min-width="180" />
            <el-table-column prop="room_no" label="房间" width="100" />
            <el-table-column label="金额" width="120">
              <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
            </el-table-column>
            <el-table-column label="支付方式" width="120">
              <template #default="{ row }">{{ PAY_METHOD_LABELS[row.pay_method] }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }"><StatusTag :value="row.status" /></template>
            </el-table-column>
            <el-table-column label="支付时间" min-width="170">
              <template #default="{ row }">{{ formatDateTime(row.paid_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button v-if="row.status === 'pending'" link type="success" @click="payRecharge(row, true)">支付</el-button>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog v-model="billVisible" title="生成月度水电账单" width="620px" destroy-on-close>
      <el-form ref="billFormRef" :model="billForm" :rules="billRules" label-position="top">
        <div class="form-grid">
          <el-form-item label="房间" prop="room_id">
            <el-select v-model="billForm.room_id" filterable style="width: 100%">
              <el-option v-for="room in rooms" :key="room.id" :label="`${room.building_name} · ${room.room_no}`" :value="room.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="账单月份" prop="bill_month">
            <el-date-picker v-model="billForm.bill_month" type="month" value-format="YYYY-MM" style="width: 100%" />
          </el-form-item>
          <el-form-item label="水表上期">
            <el-input-number v-model="billForm.water_prev" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="水表本期">
            <el-input-number v-model="billForm.water_curr" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="水价（元/吨）">
            <el-input-number v-model="billForm.water_unit_price" :min="0" :precision="4" style="width: 100%" />
          </el-form-item>
          <el-form-item label="电表上期">
            <el-input-number v-model="billForm.electricity_prev" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="电表本期">
            <el-input-number v-model="billForm.electricity_curr" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="电价（元/度）">
            <el-input-number v-model="billForm.electricity_unit_price" :min="0" :precision="4" style="width: 100%" />
          </el-form-item>
          <el-form-item label="缴费截止日">
            <el-date-picker v-model="billForm.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="billVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitBill">生成账单</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rechargeVisible" title="水电充值" width="450px" destroy-on-close>
      <div class="recharge-room">
        <span>充值房间</span>
        <strong>{{ rechargeAccount?.building_name }} · {{ rechargeAccount?.room_no }}</strong>
        <small>当前余额 {{ formatMoney(rechargeAccount?.balance) }}</small>
      </div>
      <el-form label-position="top">
        <el-form-item label="充值金额">
          <el-input-number v-model="rechargeForm.amount" :min="1" :max="100000" :precision="2" style="width: 100%" />
          <div class="amount-presets">
            <el-button v-for="amount in [20, 50, 100, 200]" :key="amount" size="small" @click="rechargeForm.amount = amount">
              ¥{{ amount }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="支付方式">
          <el-radio-group v-model="rechargeForm.pay_method">
            <el-radio-button value="wechat_mock">模拟微信</el-radio-button>
            <el-radio-button value="alipay_mock">模拟支付宝</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <div class="mock-tip">
        <el-icon><InfoFilled /></el-icon>
        这是模拟充值，不会产生真实支付。点击确认后订单会直接标记为支付成功。
      </div>
      <template #footer>
        <el-button @click="rechargeVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitRecharge">确认支付</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="txVisible" title="账户流水" size="460px">
      <div v-if="txAccount" class="tx-head">
        <div>
          <div class="tx-room">{{ txAccount.building_name }} · {{ txAccount.room_no }}</div>
          <div class="muted">当前余额 {{ formatMoney(txAccount.balance) }}</div>
        </div>
      </div>
      <el-table v-loading="txLoading" :data="transactions" size="small">
        <el-table-column label="时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ txLabel(row.type) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }">
            <span :class="Number(row.amount) >= 0 ? 'tx-in' : 'tx-out'">
              {{ Number(row.amount) >= 0 ? '+' : '' }}{{ formatMoney(row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="余额" width="110">
          <template #default="{ row }">{{ formatMoney(row.balance_after) }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import PageHeader from '@/components/PageHeader.vue'
import StatusTag from '@/components/StatusTag.vue'
import { excelApi, roomApi, utilityApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import {
  PAY_METHOD_LABELS,
  formatDateTime,
  formatMoney,
} from '@/utils/constants'

const auth = useAuthStore()
const tab = ref('accounts')
const accounts = ref([])
const bills = ref([])
const recharges = ref([])
const rooms = ref([])
const loading = reactive({ accounts: false, bills: false, recharges: false })
const saving = ref(false)

const billVisible = ref(false)
const rechargeVisible = ref(false)
const txVisible = ref(false)
const txLoading = ref(false)
const txAccount = ref(null)
const transactions = ref([])
const rechargeAccount = ref(null)
const billFormRef = ref()
const billForm = reactive({
  room_id: null,
  bill_month: '',
  water_prev: 0,
  water_curr: 0,
  water_unit_price: 3.5,
  electricity_prev: 0,
  electricity_curr: 0,
  electricity_unit_price: 0.6,
  due_date: '',
})
const billRules = {
  room_id: [{ required: true, message: '请选择房间', trigger: 'change' }],
  bill_month: [{ required: true, message: '请选择账单月份', trigger: 'change' }],
}
const rechargeForm = reactive({ amount: 50, pay_method: 'wechat_mock' })

const totalBalance = computed(() =>
  accounts.value.reduce((sum, item) => sum + Number(item.balance || 0), 0),
)
const unpaidCount = computed(() => bills.value.filter((b) => b.status === 'unpaid').length)
const monthRecharge = computed(() => {
  const month = new Date().toISOString().slice(0, 7)
  return recharges.value
    .filter((r) => r.status === 'success' && (r.paid_at || '').startsWith(month))
    .reduce((sum, r) => sum + Number(r.amount || 0), 0)
})

function txLabel(type) {
  return { recharge: '充值', bill_payment: '缴费', adjustment: '调整', refund: '退款' }[type] || type
}

async function loadTab() {
  if (tab.value === 'accounts') await loadAccounts()
  else if (tab.value === 'bills') await loadBills()
  else await loadRecharges()
}

async function loadAccounts() {
  loading.accounts = true
  try {
    const { data } = await utilityApi.accounts({ page_size: 100 })
    accounts.value = data.items
  } finally {
    loading.accounts = false
  }
}

async function loadBills() {
  loading.bills = true
  try {
    const { data } = await utilityApi.bills({ page_size: 100 })
    bills.value = data.items
  } finally {
    loading.bills = false
  }
}

async function loadRecharges() {
  loading.recharges = true
  try {
    const { data } = await utilityApi.recharges({ page_size: 100 })
    recharges.value = data.items
  } finally {
    loading.recharges = false
  }
}

async function loadRooms() {
  if (auth.isStudent) return
  const { data } = await roomApi.list({ page_size: 100 })
  rooms.value = data.items
}

function openBill() {
  Object.assign(billForm, {
    room_id: rooms.value[0]?.id || null,
    bill_month: new Date().toISOString().slice(0, 7),
    water_prev: 0,
    water_curr: 0,
    water_unit_price: 3.5,
    electricity_prev: 0,
    electricity_curr: 0,
    electricity_unit_price: 0.6,
    due_date: '',
  })
  billVisible.value = true
}

async function submitBill() {
  try {
    await billFormRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await utilityApi.createBill({
      room_id: billForm.room_id,
      bill_month: `${billForm.bill_month}-01`,
      water_prev: billForm.water_prev,
      water_curr: billForm.water_curr,
      water_unit_price: billForm.water_unit_price,
      electricity_prev: billForm.electricity_prev,
      electricity_curr: billForm.electricity_curr,
      electricity_unit_price: billForm.electricity_unit_price,
      due_date: billForm.due_date || null,
    })
    ElMessage.success('账单已生成')
    billVisible.value = false
    tab.value = 'bills'
    await Promise.all([loadBills(), loadAccounts()])
  } finally {
    saving.value = false
  }
}

function openRecharge(account) {
  rechargeAccount.value = account
  rechargeForm.amount = 50
  rechargeForm.pay_method = 'wechat_mock'
  rechargeVisible.value = true
}

async function submitRecharge() {
  if (!rechargeForm.amount || rechargeForm.amount <= 0) {
    ElMessage.warning('请输入充值金额')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认模拟支付 ${formatMoney(rechargeForm.amount)} 到 ${rechargeAccount.value.room_no} 房间？`,
      '模拟支付',
      { type: 'info' },
    )
  } catch {
    return
  }
  saving.value = true
  try {
    const created = await utilityApi.createRecharge({
      account_id: rechargeAccount.value.id,
      amount: rechargeForm.amount,
      pay_method: rechargeForm.pay_method,
    })
    await utilityApi.payRecharge(created.data.id)
    ElMessage.success('充值成功')
    rechargeVisible.value = false
    await Promise.all([loadAccounts(), loadRecharges()])
  } finally {
    saving.value = false
  }
}

async function payRecharge(row, direct = false) {
  try {
    if (!direct) {
      await ElMessageBox.confirm(`确认支付订单 ${row.order_no}？`, '模拟支付', { type: 'info' })
    }
    await utilityApi.payRecharge(row.id)
    ElMessage.success('支付成功')
    await Promise.all([loadRecharges(), loadAccounts()])
  } catch {
    // 取消
  }
}

async function payBill(row) {
  try {
    await ElMessageBox.confirm(
      `确认从房间余额缴纳 ${formatMoney(row.total_amount)}？`,
      '账单缴费',
      { type: 'info' },
    )
    await utilityApi.payBill(row.id)
    ElMessage.success('缴费成功')
    await Promise.all([loadBills(), loadAccounts()])
  } catch {
    // 取消
  }
}

async function openTransactions(account) {
  txAccount.value = account
  txVisible.value = true
  txLoading.value = true
  try {
    const { data } = await utilityApi.transactions(account.id, { page_size: 100 })
    transactions.value = data.items
  } finally {
    txLoading.value = false
  }
}

onMounted(async () => {
  await loadRooms()
  await loadAccounts()
  await loadBills()
  await loadRecharges()
})
</script>

<style scoped>
.utility-summary {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 18px 20px;
  color: var(--dms-ink);
  background: #ffffff;
  border: 1px solid var(--dms-line);
  border-top-color: var(--dms-ink);
  border-radius: 5px;
}
.summary-main {
  display: flex;
  align-items: center;
  gap: 13px;
  padding-right: 26px;
  border-right: 1px solid var(--dms-line);
}
.summary-icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #5c5c5c;
  background: transparent;
  border: 1px solid var(--dms-line);
  border-radius: 2px;
  font-size: 16px;
}
.summary-label {
  color: var(--dms-muted);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.02em;
  text-transform: none;
}
.summary-value {
  margin-top: 5px;
  color: var(--dms-ink);
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.04em;
}
.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--dms-muted);
  font-size: 10px;
}
.summary-item strong {
  color: var(--dms-ink);
  font-size: 15px;
  font-weight: 600;
}
.balance-text {
  color: #111111;
  font-weight: 700;
}
.recharge-room {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 16px;
  padding: 13px;
  background: #f7f7f7;
  border: 1px solid #ececec;
  border-radius: 3px;
}
.recharge-room span {
  color: #999999;
  font-size: 10px;
}
.recharge-room strong {
  color: #111111;
  font-size: 16px;
  font-weight: 600;
}
.recharge-room small {
  color: #6b6b6b;
  font-size: 10px;
}
.amount-presets {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.mock-tip {
  display: flex;
  gap: 7px;
  padding: 10px;
  color: #707070;
  background: #f7f7f7;
  border: 1px solid #ececec;
  border-radius: 3px;
  font-size: 10px;
  line-height: 1.6;
}
.mock-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: #555555;
}
.tx-head {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--dms-line);
}
.tx-room {
  margin-bottom: 4px;
  color: var(--dms-ink);
  font-size: 16px;
  font-weight: 650;
}
.tx-in {
  color: var(--dms-success);
  font-weight: 600;
}
.tx-out {
  color: var(--dms-danger);
  font-weight: 600;
}
@media (max-width: 700px) {
  .utility-summary {
    align-items: flex-start;
    flex-direction: column;
  }
  .summary-main {
    padding-right: 0;
    padding-bottom: 14px;
    border-right: 0;
    border-bottom: 1px solid var(--dms-line);
  }
}
</style>
