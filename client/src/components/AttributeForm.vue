<script setup lang="ts">
import { ref } from 'vue'
import type { AttributeDefinition } from '@/services'

type AttributeField = {
  id: number
  name: string
  type: AttributeDefinition['type']
  min: number | string
  max: number | string
  categories: string
}

let nextAttributeId = 0
const attributes = ref<AttributeField[]>([])

const addAttribute = () => {
  attributes.value.push({
    id: nextAttributeId++,
    name: '',
    type: 'string',
    min: 0,
    max: 10,
    categories: '',
  })
}

const categoryOptions = (value: string) => [
  ...new Set(
    value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean),
  ),
]

const getDefinitions = (): AttributeDefinition[] => {
  const names = new Set<string>()

  return attributes.value.map((field) => {
    const name = field.name.trim()
    if (!name || names.has(name) || ['id', 'pipeset_id', 'geometry'].includes(name)) {
      throw new Error('Attribute names must be non-empty, unique, and not reserved.')
    }
    names.add(name)

    if (field.type === 'string' || field.type === 'number') {
      if (
        !Number.isSafeInteger(field.min) ||
        !Number.isSafeInteger(field.max) ||
        Number(field.min) > Number(field.max) ||
        (field.type === 'string' && Number(field.min) < 0)
      ) {
        throw new Error(`Invalid minimum or maximum for attribute ${name}.`)
      }

      return { name, type: field.type, min: Number(field.min), max: Number(field.max) }
    }

    if (field.type === 'category') {
      const categories = categoryOptions(field.categories)

      if (!categories.length) {
        throw new Error(`At least one category is required for ${name}.`)
      }

      return { name, type: field.type, categories }
    }

    return { name, type: field.type }
  })
}

defineExpose({ getDefinitions })
</script>

<template>
  <div class="attribute-form">
    <div>Attributes (optional)</div>
    <div v-for="field in attributes" :key="field.id" class="attribute-fields">
      <label :for="`attribute-name-${field.id}`">Field name</label>
      <input :id="`attribute-name-${field.id}`" v-model="field.name" type="text" />
      <label :for="`attribute-type-${field.id}`">Field type</label>
      <select :id="`attribute-type-${field.id}`" v-model="field.type">
        <option value="string">String</option>
        <option value="number">Number (integer)</option>
        <option value="boolean">Boolean</option>
        <option value="category">Category (string)</option>
      </select>
      <template v-if="field.type === 'string' || field.type === 'number'">
        <label :for="`attribute-min-${field.id}`">{{
          field.type === 'string' ? 'Minimum length' : 'Minimum value'
        }}</label>
        <input
          :id="`attribute-min-${field.id}`"
          v-model.number="field.min"
          type="number"
          step="1"
          :min="field.type === 'string' ? 0 : undefined"
        />
        <label :for="`attribute-max-${field.id}`">{{
          field.type === 'string' ? 'Maximum length' : 'Maximum value'
        }}</label>
        <input
          :id="`attribute-max-${field.id}`"
          v-model.number="field.max"
          type="number"
          step="1"
          :min="field.type === 'string' ? 0 : undefined"
        />
      </template>
      <template v-else-if="field.type === 'category'">
        <label :for="`attribute-categories-${field.id}`"
          >Categories (comma-separated; commas cannot be part of a category)</label
        >
        <input :id="`attribute-categories-${field.id}`" v-model="field.categories" type="text" />
        <div>Options: {{ categoryOptions(field.categories).join(', ') }}</div>
      </template>
      <button type="button" @click="attributes = attributes.filter((item) => item.id !== field.id)">
        Remove attribute
      </button>
    </div>
    <button type="button" @click="addAttribute">Add attribute</button>
  </div>
</template>

<style scoped>
.attribute-form,
.attribute-fields {
  display: flex;
  flex-direction: column;
}
</style>
