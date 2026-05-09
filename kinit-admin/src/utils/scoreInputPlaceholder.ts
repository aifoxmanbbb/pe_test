type ScoreInputItem = {
  label?: string
  value?: string
  item_name?: string
  calc_mode?: string | null
}

const includesAny = (text: string, keywords: string[]) => keywords.some((keyword) => text.includes(keyword))

const getItemName = (item?: ScoreInputItem | null) => String(item?.item_name || item?.label || '').trim()

export const getScoreInputPlaceholder = (item?: ScoreInputItem | null) => {
  if (!item) return '请输入成绩'

  const code = String(item.value || '').toLowerCase()
  const name = getItemName(item)
  const signature = `${code} ${name}`.toLowerCase()

  if (code === 'height' || includesAny(signature, ['身高'])) {
    return '请输入身高，单位：cm'
  }
  if (code === 'weight' || includesAny(signature, ['体重'])) {
    return '请输入体重，单位：kg'
  }
  if (code === 'bmi' || includesAny(signature, ['bmi'])) {
    return '请输入BMI值'
  }
  if (code === 'lung' || includesAny(signature, ['肺活量'])) {
    return '请输入肺活量，单位：ml'
  }
  if (code === 'sit' || includesAny(signature, ['坐位体前屈'])) {
    return `请输入${name || '成绩'}，单位：cm，可为负数`
  }
  if (includesAny(signature, ['跳绳', '引体向上', '仰卧起坐']) || includesAny(code, ['rope', 'pull_up', 'sit_up'])) {
    return `请输入${name || '成绩'}，单位：次`
  }
  if (includesAny(signature, ['跳远', '实心球', '掷实心球']) || includesAny(code, ['jump', 'ball'])) {
    return `请输入${name || '成绩'}，单位：米`
  }
  if (
    includesAny(signature, ['跑', '游泳', '50米', '100米', '800米', '1000米']) ||
    includesAny(code, ['run', '50m', '100m', '800m', '1000m', 'swim'])
  ) {
    return `请输入${name || '成绩'}，单位：秒或分秒，如 12.5 或 3'20`
  }
  if (String(item.calc_mode || '').toLowerCase() === 'record') {
    return `请输入${name || '原始测量值'}`
  }
  return '请输入原始成绩'
}
