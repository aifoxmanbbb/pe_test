<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    value: number | string
    decimals?: number
    duration?: number
    suffix?: string
    prefix?: string
  }>(),
  {
    decimals: 0,
    duration: 1200,
    suffix: '',
    prefix: ''
  }
)

const displayValue = ref(0)
let frameId = 0

const numericValue = computed(() => {
  const parsed = Number(props.value)
  return Number.isFinite(parsed) ? parsed : null
})

const formatValue = (value: number) => {
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals
  })
}

const stopAnimation = () => {
  if (frameId) {
    cancelAnimationFrame(frameId)
    frameId = 0
  }
}

const animateTo = (target: number) => {
  stopAnimation()
  const start = displayValue.value
  const delta = target - start
  const begin = performance.now()

  const tick = (now: number) => {
    const progress = Math.min((now - begin) / props.duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    displayValue.value = start + delta * eased
    if (progress < 1) {
      frameId = requestAnimationFrame(tick)
    }
  }

  frameId = requestAnimationFrame(tick)
}

watch(
  numericValue,
  (value) => {
    if (value === null) return
    animateTo(value)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  stopAnimation()
})

const textValue = computed(() => {
  if (numericValue.value === null) return `${props.prefix}${props.value}${props.suffix}`
  return `${props.prefix}${formatValue(displayValue.value)}${props.suffix}`
})
</script>

<template>
  <span>{{ textValue }}</span>
</template>
