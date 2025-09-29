<script setup>
import { ref } from 'vue'
import axios from 'axios'

const pdfId = ref('')
const cards = ref([])
const metrics = ref(null)
const deckName = ref('Demo Deck')

async function uploadPDF(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const form = new FormData()
  form.append('file', file)
  const { data } = await axios.post('/api/upload', form)
  pdfId.value = data.pdf_id
}

async function extract() {
  if (!pdfId.value) return
  const body = {
    filename: 'uploaded.pdf',
    language: 'en',
    card_types: ['qa', 'cloze'],
    max_cards: 50
  }
  const { data } = await axios.post(`/api/extract?pdf_id=${pdfId.value}`, body)
  cards.value = data.cards
  metrics.value = data.metrics
}

async function exportApkg() {
  if (!cards.value.length) return
  const { data } = await axios.post(
    '/api/export.apkg',
    { deck_name: deckName.value, cards: cards.value },
    { responseType: 'blob' }
  )
  const url = URL.createObjectURL(new Blob([data]))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${deckName.value}.apkg`
  anchor.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="max-w-5xl mx-auto p-6 space-y-6">
    <header class="space-y-2">
      <h1 class="text-3xl font-bold">PDF → Anki Cards</h1>
      <p class="text-gray-600">
        Upload your course PDF, generate candidate cards, review them, then export directly to
        Anki.
      </p>
    </header>

    <section class="flex flex-wrap items-center gap-4">
      <input
        type="file"
        accept="application/pdf"
        @change="uploadPDF"
        class="block"
      />
      <button
        class="px-4 py-2 rounded bg-black text-white disabled:opacity-40"
        :disabled="!pdfId"
        @click="extract"
      >
        Extract
      </button>
    </section>

    <section v-if="metrics" class="text-sm text-gray-600">
      Pages: {{ metrics.pages }} — Candidates: {{ metrics.candidates }}
    </section>

    <section class="flex items-center gap-3">
      <label class="text-sm">Deck name</label>
      <input v-model="deckName" class="border rounded px-2 py-1" />
      <button
        class="px-3 py-1 rounded bg-emerald-600 text-white disabled:opacity-40"
        :disabled="!cards.length"
        @click="exportApkg"
      >
        Export .apkg
      </button>
    </section>

    <section class="grid gap-4 md:grid-cols-2">
      <article v-for="card in cards" :key="card.id" class="p-4 border rounded space-y-2">
        <div class="text-xs uppercase text-gray-500">
          {{ card.type.toUpperCase() }} — p.{{ card.source_page }} — conf
          {{ Math.round(card.confidence * 100) }}%
        </div>
        <div class="prose" v-html="card.question"></div>
        <p v-if="card.answer" class="text-gray-800">{{ card.answer }}</p>
        <p class="text-xs text-gray-500 max-h-16 overflow-hidden">{{ card.source_snippet }}</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in card.tags"
            :key="tag"
            class="text-xs bg-gray-100 rounded px-2 py-0.5"
          >
            {{ tag }}
          </span>
        </div>
      </article>
    </section>
  </div>
</template>
