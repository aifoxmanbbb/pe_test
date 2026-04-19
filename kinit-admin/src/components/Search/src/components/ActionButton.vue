<script setup lang="ts">
import { useIcon } from '@/hooks/web/useIcon'
import { propTypes } from '@/utils/propTypes'
import { useI18n } from '@/hooks/web/useI18n'

const emit = defineEmits(['search', 'reset', 'expand'])

const { t } = useI18n()

defineProps({
  showSearch: propTypes.bool.def(true),
  showReset: propTypes.bool.def(true),
  showExpand: propTypes.bool.def(false),
  searchButtonCircle: propTypes.bool.def(false),
  searchButtonIconOnly: propTypes.bool.def(false),
  searchButtonClass: propTypes.string.def(''),
  searchButtonIcon: propTypes.string.def('ep:search'),
  visible: propTypes.bool.def(true),
  searchLoading: propTypes.bool.def(false),
  resetLoading: propTypes.bool.def(false)
})

const onSearch = () => {
  emit('search')
}

const onReset = () => {
  emit('reset')
}

const onExpand = () => {
  emit('expand')
}
</script>

<template>
  <BaseButton
    v-if="showSearch && searchButtonIconOnly"
    type="primary"
    :circle="searchButtonCircle"
    :class="searchButtonClass"
    :loading="searchLoading"
    :icon="useIcon({ icon: searchButtonIcon })"
    @click="onSearch"
  />
  <BaseButton
    v-else-if="showSearch"
    type="primary"
    :circle="searchButtonCircle"
    :class="searchButtonClass"
    :loading="searchLoading"
    :icon="useIcon({ icon: searchButtonIcon })"
    @click="onSearch"
  >
    {{ t('common.query') }}
  </BaseButton>
  <BaseButton
    v-if="showReset"
    :loading="resetLoading"
    :icon="useIcon({ icon: 'ep:refresh-right' })"
    @click="onReset"
  >
    {{ t('common.reset') }}
  </BaseButton>
  <BaseButton
    v-if="showExpand"
    :icon="useIcon({ icon: visible ? 'ep:arrow-up' : 'ep:arrow-down' })"
    text
    @click="onExpand"
  >
    {{ t(visible ? 'common.shrink' : 'common.expand') }}
  </BaseButton>
</template>
